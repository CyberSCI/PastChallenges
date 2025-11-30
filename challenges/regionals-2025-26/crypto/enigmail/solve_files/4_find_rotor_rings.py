from enigma.machine import EnigmaMachine

CIPHERTEXT = 'PFDDHAILTMKJRQNTCKNKLOJEHOJZBJBGOTBAIWRSXXOKKUQRNYQMJUZCCKLMDCCZNZWGIWQFXGDUURPYOFBXJYEDDRKUSMFOTGIODPGRWNSGQYGSEXSAKTOEJZLGDPFJBIASVSJSRKCPACQKAUYJMZDJQQMMZGUMGXGRGNJIUECAIVKMHKNRSCNHIXRXXYGKZXDSOKJVIFDPIHBTRWBZKIKKFHVDLEHQUAINUXOXCUMJIJSXNJRRBYKMCBRCKTNGBZQREPJKKIVNAKBSJSOAPPAIGVPOVOLPFNBHHZTMZXODUSBZLDUZQAJUMIAHVUSQYPTSXXBJWUUKDJRAKUQZEOTVGQNGKSGUXWCHXNCUPNLJRWUQEZICOZXTASZGGIQLWDKBRLAMRWPTKXBJSUYCGMDKKRKPOMGOYHQBXPTKVYQCBMWCTVJHBJJOUESLRFTBGNJNPYXOAFMRAFXBTFTSOWBCCFILYXZGXKGDUYNSLRFKPBFWWINI'
PLAINTEXT  = 'GJFGECEPFCHHDAELEHGHGPEBEBEBEBEOFDFFGIEFFFGHEBEBECHGFFEBEBEBEIFIEDEBFJEBEBEBEDENEGDJGBHGEBEBEBEBEBFIEOFDFCDAEJEBHCHDDEGDDGFBEBEBEBEBFCGOFBFFDBECEBEBEDHIANAKGKHHHGDIFJFBFFEBEBEBEBEKGDEFGIFKGDHHEBEBEMGJEJEBEBEDDEGJEBGBHCGJDDFKEJEBEBEBEBFKGEEFFGFJGEEGEOHGFKGOFCDDFJFIEKGMEBEIGEDDGEHJDFHAGCGNHEHKFJDCEGHHFKFDDFHGANAKGDGNGFGCDHGKHHGBEBEBEBEBEEGOFCEGFHEIFCFFGBFIFCHDFKFBECEEGFFHEKGMGDGMEOGKGBGEGNHBEGHIENEBEBENEJGMFDFFFCECFGEIGIGFDHEKDAEGHFEDDBFGCPGCCPGOFIHCHAECEHHBFCECANAKFDGLEHFBEFGIEBEFFFFCGPGMEGEFFCEF'

# From CyberChef's Multiple Bombe analysis
rotors = 'V IV I'
ring_settings = 'A A W'
initial_positions = 'ROV'
reflector = 'B'
plugboard_settings = 'FH AN BJ CK DD EO GW IR LL MQ PP TZ SU'

offset_rotor_index = 1

# Remove same-letter plugboard connections
plugboard_settings = ' '.join([pair for pair in plugboard_settings.split() if pair[0] != pair[1]])

print(plugboard_settings)

def decrypt(ring_settings, initial_positions):
    machine = EnigmaMachine.from_key_sheet(
        rotors=rotors,
        reflector=reflector,
        ring_settings=ring_settings,
        plugboard_settings=plugboard_settings
    )
    
    machine.set_display(initial_positions)
    
    return machine.process_text(CIPHERTEXT)

for i in range(26):
    # Increment ring setting
    offset_ring_settings = ring_settings.split(' ')
    offset_ring_settings[offset_rotor_index] = chr(((ord(offset_ring_settings[offset_rotor_index]) - ord('A') + i) % 26) + ord('A'))
    offset_ring_settings = ' '.join(offset_ring_settings)
    
    # Increment initial position
    offset_initial_positions = list(initial_positions)
    offset_initial_positions[offset_rotor_index] = chr(((ord(offset_initial_positions[offset_rotor_index]) - ord('A') + i) % 26) + ord('A'))
    offset_initial_positions = ''.join(offset_initial_positions)
    
    # Decrypt with modified settings
    decrypted_text = decrypt(offset_ring_settings, offset_initial_positions)
    
    # Compare decrypted text with known plaintext
    likeness = sum(1 for i, j in zip(decrypted_text, PLAINTEXT) if i == j)

    print(f'Ring Settings: {offset_ring_settings}, Initial Positions: {offset_initial_positions} => Likeness: {likeness}')