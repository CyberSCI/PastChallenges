all: vts.db vts.luc

# Build the database
vts.db: 
	python3 prepare-data.py

# Obfuscate names in the source code to make analysis more difficult
vts_obfuscated.lua: vts.lua
	cp $< $@
	sed -i "s/\bsocket_lib\b/a1/g" $@
	sed -i "s/\bssl_lib\b/a2/g" $@
	sed -i "s/\bsqlite_lib\b/a3/g" $@
	sed -i "s/\bsignal_lib\b/a4/g" $@
	sed -i "s/\bcrc_lib\b/a5/g" $@
	sed -i "s/\bVOTES_ACCEPTED\b/a6/g" $@
	sed -i "s/\bVOTES_REJECTED\b/a7/g" $@
	sed -i "s/\bWIDTH\b/a8/g" $@
	sed -i "s/\bglobal_voters\b/a9/g" $@
	sed -i "s/\bglobal_machines\b/a10/g" $@
	sed -i "s/\bcontinue_listening\b/a11/g" $@
	sed -i "s/\bexit_method\b/a12/g" $@
	sed -i "s/\brun_as_service\b/a13/g" $@
	sed -i "s/\bbanner\b/a14/g" $@
	sed -i "s/\bfooter\b/a15/g" $@
	sed -i "s/\binit\b/a16/g" $@
	sed -i "s/\benv\b/a17/g" $@
	sed -i "s/\bdb_connection\b/a18/g" $@
	sed -i "s/\bresults\b/a19/g" $@
	sed -i "s/\bvoter_full_name\b/a20/g" $@
	sed -i "s/\bcrc_value\b/a21/g" $@
	sed -i "s/\bforeground\b/a22/g" $@
	sed -i "s/\bbackground\b/a23/g" $@
	sed -i "s/\bshutdown\b/a24/g" $@
	sed -i "s/\bread_uint32\b/a25/g" $@
	sed -i "s/\bval_uint32\b/a26/g" $@
	sed -i "s/\bread_int8\b/a27/g" $@
	sed -i "s/\bval_int8\b/a28/g" $@
	sed -i "s/\bread_str\b/a29/g" $@
	sed -i "s/\bstr_len\b/a30/g" $@
	sed -i "s/\bread_chars\b/a31/g" $@
	sed -i "s/\bval_str\b/a32/g" $@
	sed -i "s/\bchar_num\b/a33/g" $@
	sed -i "s/\bread_package\b/a34/g" $@
	sed -i "s/\bpackage_instance\b/a35/g" $@
	sed -i "s/\bmachine_id\b/a36/g" $@
	sed -i "s/\bvotes_in_package\b/a37/g" $@
	sed -i "s/\bvote_records\b/a38/g" $@
	sed -i "s/\bsingle_record\b/a39/g" $@
	sed -i "s/\bcandidate_id\b/a40/g" $@
	sed -i "s/\bcandidate_name\b/a41/g" $@
	sed -i "s/\bvoter_id\b/a42/g" $@
	sed -i "s/\bvoter_name\b/a43/g" $@
	sed -i "s/\bvote_value\b/a44/g" $@
	sed -i "s/\bpackage_verified\b/a45/g" $@
	sed -i "s/\bpackage_to_check\b/a46/g" $@
	sed -i "s/\bvote_rec\b/a47/g" $@
	sed -i "s/\bvote_num\b/a48/g" $@
	sed -i "s/\bapply_votes\b/a49/g" $@
	sed -i "s/\bloaded_package\b/a50/g" $@
	sed -i "s/\bvote_record\b/a51/g" $@
	sed -i "s/\bcurrent_vote_count\b/a52/g" $@
	sed -i "s/\bcolor\b/a53/g" $@
	sed -i "s/\bfore\b/a54/g" $@
	sed -i "s/\bback\b/a55/g" $@
	sed -i "s/\bdisplay_results\b/a56/g" $@
	sed -i "s/\bvotes_map\b/a57/g" $@
	sed -i "s/\bcand_name\b/a58/g" $@
	sed -i "s/\bcandidate_vote_count\b/a59/g" $@
	sed -i "s/\bmax_count\b/a60/g" $@
	sed -i "s/\bcandidate_no\b/a61/g" $@
	sed -i "s/\bbar\b/a62/g" $@
	sed -i "s/\bparams\b/a63/g" $@
	sed -i "s/\bmain\b/a64/g" $@
	sed -i "s/\bserver_instance\b/a65/g" $@
	sed -i "s/\bbind_result\b/a66/g" $@
	sed -i "s/\bbind_err\b/a67/g" $@
	sed -i "s/\blisten_result\b/a68/g" $@
	sed -i "s/\blisten_err\b/a69/g" $@
	sed -i "s/\bconn\b/a70/g" $@
	sed -i "s/\breceived_package\b/a71/g" $@
	sed -i "s/\bverified\b/a72/g" $@

# Compile obfuscated source
vts.luc: vts_obfuscated.lua
	luac5.3 -o $@ $<
