-- CyberSci Nationals 2024/25
--
-- Vote Tabulation Service by 0xd13a

-- Import necessary libraries
local socket_lib = require("socket")
local ssl_lib = require("ssl")
local sqlite_lib = require("luasql.sqlite3")
local signal_lib = require("posix.signal")
local crc_lib = require("crc32")

-- Result codes to return on response
VOTES_ACCEPTED = "\x01"
VOTES_REJECTED = "\x00"

-- Expected width of the text terminal
WIDTH = 100

-- Known voters
local global_voters = {}

-- Known voting machines
local global_machines = {}

-- Should we contrinue listening for requests or exit
continue_listening = true

-- Ctrl+C handler
exit_method = function(num)
    continue_listening = false
end

-- Should we run as a service or interactive?
run_as_service = false

-- Informational messages
banner = "              *** Val Verde Central Electoral Commission * Vote Tabulation Service ***              "
footer = " Press Ctrl+C to exit                                                                               "

-- Initialize the system
function init()
    -- Check command line arguments
    if arg[1] == "-s" then
        run_as_service = true
        print(banner)
        print(footer)
    end

    -- Set up an exit handler
    signal_lib.signal(signal_lib.SIGINT, exit_method)

    -- Initialize database reader
    env = sqlite_lib.sqlite3()
    db_connection = env:connect("./vts.db")

    -- Load voters
    local results = db_connection:execute("SELECT name FROM voters;")
    local voter_full_name = results:fetch()
    while voter_full_name do
        global_voters[voter_full_name] = true
        voter_full_name = results:fetch()
    end
    results:close()

    -- Load machine ID checksums
    local crc_value
    results = db_connection:execute("SELECT crc FROM machines;")
    crc_value = results:fetch()
    while crc_value do
        global_machines[crc_value] = true
        crc_value = results:fetch()
    end
    results:close()
end

-- Foreground color codes
local foreground = {
    [0] = 31,
    [1] = 32,
    [2] = 33,
    [3] = 34,
    [4] = 35,
    [5] = 31,
    [6] = 32,
    [7] = 33,
    [8] = 34,
    [9] = 35
}

-- Background machine codes
local background = {
    [0] = 41,
    [1] = 42,
    [2] = 43,
    [3] = 44,
    [4] = 45,
    [5] = 41,
    [6] = 42,
    [7] = 43,
    [8] = 44,
    [9] = 45
}

-- Shutdown operation
function shutdown()
    db_connection:close()
    env:close()
end

-- Read unsigned 32-bit int
function read_uint32(c)
    local val_uint32 = c:receive(4)
    return string.unpack("<I4", val_uint32)
end

-- Read signed 8-bit int
function read_int8(c)
    local val_int8 = c:receive(1)
    return string.unpack("<i1", val_int8)
end

-- Read string (preceded by length code)
function read_str(c)
    local str_len = read_int8(c)
    return read_chars(c,str_len)
end

-- Read specified number of chars
function read_chars(c,char_num)
    local val_str = c:receive(char_num)
    return string.unpack("c" .. tostring(char_num), val_str)
end

-- Read vote result package
function read_package(c)
    local package_instance = {}
    package_instance["machine_id"] = read_chars(c, 16)
    local votes_in_package = read_int8(c)
    local vote_records = {}
    for i=1,votes_in_package do
        local single_record = {}
        single_record["candidate_id"] = read_int8(c)
        single_record["candidate_name"] = read_str(c)
        single_record["voter_id"] = read_uint32(c)
        single_record["voter_name"] = read_str(c)
        single_record["vote_value"] = read_int8(c)
        vote_records[i] = single_record
    end
    package_instance["vote_records"] = vote_records
    return package_instance
end

-- Verify vote package
function package_verified(package_to_check)

    -- Check that machine is known
    if not global_machines[crc_lib.crc32(0,package_to_check["machine_id"])] then
        return false
    end

    for i=1,#package_to_check["vote_records"] do
        local vote_rec = package_to_check["vote_records"][i]

        -- Check candidate is real
        local results = db_connection:execute("SELECT votes FROM candidates WHERE name='" .. vote_rec["candidate_name"] .. "';")
        local vote_num = results:fetch()
        if not vote_num then
            results:close()
            return false
        end

        -- Check voter is known
        if not global_voters[vote_rec["voter_name"]] then 
            return false
        end

        -- Check that we have a single vote
        if vote_rec["vote_value"] > 1 then
            return false
        end
    end
    return true
end

-- Apply votes to the global database
function apply_votes(loaded_package)
    for i=1,#loaded_package["vote_records"] do
        local vote_record = loaded_package["vote_records"][i]

        -- Find the candidate and load current count
        local results = db_connection:execute("SELECT votes FROM candidates WHERE name='" .. vote_record["candidate_name"] .. "';")
        local current_vote_count = results:fetch()
        results:close()

        -- Increment count
        current_vote_count = current_vote_count + vote_record["vote_value"]

        -- Apply count to the voter
        results = db_connection:execute("UPDATE candidates SET votes=" .. tostring(current_vote_count) .. " WHERE name='" .. vote_record["candidate_name"] .. "';")
    end
end

-- Create colored string prefix
function color(fore, back)
    return "\x1b[" .. tostring(fore) .. ";" .. tostring(back) .. "m"
end

-- Display results on screen (when configured)
function display_results()
    if not run_as_service then

        -- Load current votes from the database
        local votes_map = {}
        local results = db_connection:execute("SELECT name, votes FROM candidates;")
        local cand_name, candidate_vote_count = results:fetch()
        while cand_name do
            votes_map[cand_name] = candidate_vote_count
            cand_name, candidate_vote_count = results:fetch()
        end
        results:close()

        -- Intitalize screen
        print("\x1b[2J")
        print("\x1b[H")

        print(color(30, 47) .. banner .. color(37, 40))

        -- Determine vote scale 
        local max_count = 0
        for _, candidate_vote_count in pairs(votes_map) do 
            if candidate_vote_count > max_count then
                max_count = candidate_vote_count
            end
        end
        local candidate_no = 0
        -- Draw results and colored bars
        for cand_name, candidate_vote_count in pairs(votes_map) do 
            print(color(foreground[candidate_no], 40) .. cand_name .. " " .. tostring(candidate_vote_count) .. color(37, 40))

            local bar = ""
            if candidate_vote_count > 0 then
                for i=1,(WIDTH * (candidate_vote_count/max_count)) do
                    bar = bar .. " "
                end
                print(color(30, background[candidate_no]) .. bar .. color(37, 40))
            else
                print()
            end
            candidate_no = candidate_no + 1
        end
        print(color(30, 47) .. footer .. color(37, 40))
    end
end

-- TLS/SSL server parameters (omitted)
local params = {
    mode = "server",
    protocol = "tlsv1_2",
    key = "./key.pem",
    certificate = "./cert.pem",
    options = "all"
}

-- Main function
function main()
    init()

    -- Listen on the socket
    local server_instance = socket_lib.tcp()
    server_instance:setoption("reuseaddr", true)
    server_instance:settimeout(1)
    local bind_result, bind_err = server_instance:bind("0.0.0.0", 10000)
    if not bind_result then 
        print(bind_err)
        return
    end
    local listen_result, listen_err = server_instance:listen()
    if not listen_result then 
        print(listen_err)
        return
    end

    -- Display current results
    display_results()

    -- Main listening loop
    while continue_listening do

        local conn = server_instance:accept()
        if conn then

            conn = ssl_lib.wrap(conn, params)
            if conn then
                conn:dohandshake()

                -- Receive votes
                local received_package = read_package(conn)
                if run_as_service then
                    print("Received package of votes from machine", received_package["machine_id"])
                end
                -- Verify votes
                local verified = package_verified(received_package)
                if verified then
                    -- Apply them if valid
                    apply_votes(received_package)
                    conn:send(VOTES_ACCEPTED)
                else
                    conn:send(VOTES_REJECTED)
                    if run_as_service then
                        print("*** Package rejected")
                    end
                end
                conn:close()

                -- Update results
                display_results()
            end
        end
    end

    print("\nExiting...")

    server_instance:close()

    shutdown()
end

main()