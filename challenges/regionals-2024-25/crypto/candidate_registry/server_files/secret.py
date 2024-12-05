FLAG = 'cybersci{pcbc_1s_n0t_cbc_dsh8sdj9}'

KEY = bytes.fromhex('a550539904373eec47da3291d805a1d7')
IV = bytes.fromhex('05ffbdd46fc19beafdd311f8aa5c5b3b')
REGISTRATION_TOKEN = '3d67f2e4e6e70e153468b24da1846a73'


if __name__ == "__main__":
    import aes
    import json
    import os
    
    KEY = os.urandom(16)
    IV = os.urandom(16)

    while True:
        try:
            REGISTRATION_TOKEN = os.urandom(16).hex()

            pt = json.dumps({
                'registration_token': REGISTRATION_TOKEN,
                'username': 'davey_jones',
                'bio': "Once in power, I shall bring Valverdian's fleet to its former glory!"
            })

            pt = pt.encode()
            

            cipher = aes.AES(KEY)
            ct = cipher.encrypt_pcbc(pt, IV)
            ct_ = ct[:80] + ct[96:112] + ct[80:96] + ct[112:]
            
            pt_ = cipher.decrypt_pcbc(ct_, IV)
            pt_ = pt_.decode('ascii', errors='ignore')
            
            print(json.loads(pt_))
            
            print('Key:  ', KEY.hex())
            print('IV:   ', IV.hex())
            print('Token:', REGISTRATION_TOKEN)
            
            break
        except KeyboardInterrupt:
            break
        except:
            continue