# CyberSci Regionals 2026/27
#
# Log Monitor by Dmitriy Beryoza (0xd13a@gmail.com)

require 'csv'

def filter(event)
  hash, value = event.get("message").split(",", 2)

  output = IO.popen("echo -n " + value + " | sha256sum", "r+") do |pipe|
    pipe.read
  end

  calculated_hash = output.split.first

  if calculated_hash != hash.downcase
    event.tag('_csvparsefailure')
    return [event]
  end

  fields = CSV.parse_line(value)
  if fields && fields.length == 9
    event.set('batchid', fields[0])
    event.set('timestamp', fields[1])
    event.set('lastname', fields[2])
    event.set('firstname', fields[3])
    event.set('loglength', fields[4].to_i)
    event.set('logdiameter', fields[5].to_i)
    event.set('numberoflogs', fields[6].to_i)
    event.set('volume', fields[7].to_i)
    event.set('timbertype', fields[8])
  else
    event.tag('_csvparsefailure')
  end
  [event]
rescue CSV::MalformedCSVError
  event.tag('_csvparsefailure')
  [event]
end
