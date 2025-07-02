from Crypto.Util.number import getPrime, GCD, inverse
import random
from secret import FLAG


CANDIDATE_COUNT = 10
TOTAL_VOTES = 250
CANDIDATES = [
    "Esteban de Souza",
    "Raphael Velasquez",
    "Joel Plata",
    "Sofia da Silva",
    "Ana Paula Espinoza",
    "Vera Gomes",
    "Xavier Gonzalez",
    "Pedro Galeano",
    "Gen. Ramon Esperanza",
    "Arius Perez"
]


def L(x, n):
    return (x - 1) // n


def lcm(a, b):
    return abs(a * b) // GCD(a, b)


def paillier_keygen(key_size):
    p = getPrime(key_size // 2)
    q = getPrime(key_size // 2)
    n = p * q

    g = n + 1
    lam = lcm(p - 1, q - 1)
    mu = inverse(L(pow(g, lam, n**2), n), n)

    return (n, g), (lam, mu)


def paillier_encrypt(pk, m, r):
    n, g = pk
    c = pow(g, m, n**2) * pow(r, n, n**2) % (n**2)
    return c


def paillier_decrypt(pk, sk, c):
    n, _ = pk
    lam, mu = sk
    m = L(pow(c, lam, n**2), n) * mu % n
    return m


def rand_r(n):
    return random.randint(1, n - 1)


class VoteRevealer:
    def __init__(self, pk, sk):
        self.pk = pk
        self.sk = sk

    def reveal_votes(self, candidate_votes):
        votes = []
        for i in range(CANDIDATE_COUNT):
            m = paillier_decrypt(self.pk, self.sk, candidate_votes[i])
            votes.append(m)
        return votes


class VoteAggregator:
    def __init__(self, pk):
        self.pk = pk
        self.encrypted_vote = 1

    def init_votes(self):
        n, _ = self.pk
        self.candidate_votes = []
        for i in range(CANDIDATE_COUNT):
            r = rand_r(n)
            c = paillier_encrypt(self.pk, 0, r)
            self.candidate_votes.append(c)

    def save_votes(self):
        return self.candidate_votes

    def load_votes(self, state):
        assert state is not None
        self.candidate_votes = state

    def validate_vote(self, encrypted_vote):
        n, g = self.pk
        C, R = encrypted_vote
        c = 1
        for i in range(CANDIDATE_COUNT):
            c = (c * C[i]) % (n**2)
        c_ = paillier_encrypt(self.pk, 1, R)
        return c == c_

    def tally_vote(self, encrypted_vote):
        n, _ = self.pk
        C, R = encrypted_vote
        if not self.validate_vote(encrypted_vote):
            return False
        for i in range(CANDIDATE_COUNT):
            self.candidate_votes[i] = (self.candidate_votes[i] * C[i]) % (n**2)
        return True


class Voter:
    def __init__(self, pk):
        self.pk = pk

    def encrypt_vote(self, selected_candidate):
        n, _ = self.pk

        vote = [0] * CANDIDATE_COUNT
        vote[selected_candidate] = 1

        C = []
        R = 1
        for m in vote:
            r = rand_r(n)
            c = paillier_encrypt(self.pk, m, r)
            C.append(c)
            R = (R * r) % n

        return C, R


def input_encrypted_vote(pk):
    try:
        n, _ = pk
        C = []
        for i in range(CANDIDATE_COUNT):
            print(f"C[{i}] = ", end="")
            C_i = int(input())
            assert 0 < C_i < n**2
            C.append(C_i)
            
        print("R = ", end="")
        R = int(input())
        assert 0 < R < n
        
        return C, R
    except:
        print("Invalid input!")
        return None


def main():
    pk, sk = paillier_keygen(1024)

    print("Welcome to the private voting system!")
    print()

    print("This system's public key is:")
    print("n =", pk[0])
    print("g =", pk[1])
    print()
    
    print("The candidates are:")
    for i, candidate in enumerate(CANDIDATES):
        print(f"{i + 1}. {candidate}")
    print()

    print("Please wait while other candidates vote...")
    print()

    vote_revealer = VoteRevealer(pk, sk)
    vote_aggregator = VoteAggregator(pk)
    vote_aggregator.init_votes()

    voter = Voter(pk)
    for i in range(TOTAL_VOTES - 1):
        selected_candidate = random.randint(0, CANDIDATE_COUNT - 1)
        while selected_candidate == 8:
            selected_candidate = random.randint(0, CANDIDATE_COUNT - 1)

        encrypted_vote = voter.encrypt_vote(selected_candidate)
        vote_aggregator.tally_vote(encrypted_vote)

    print("Please cast your *encrypted* vote.")
    encrypted_vote = input_encrypted_vote(pk)
    if encrypted_vote is not None and not vote_aggregator.tally_vote(encrypted_vote):
        print("Invalid vote!")
    print()

    print("The votes are in...")
    votes = vote_revealer.reveal_votes(vote_aggregator.candidate_votes)

    winner = [0]
    winner_votes = votes[0]
    for i in range(1, CANDIDATE_COUNT):
        if votes[i] > winner_votes:
            winner = [i]
            winner_votes = votes[i]
        elif votes[i] == winner_votes:
            winner.append(i)

    if len(winner) == 1:
        print(f"{CANDIDATES[winner[0]]} has been elected!")
        
        if winner[0] == 8:
            print(FLAG)
    else:
        print("It's a tie! A rerun will be held.")


if __name__ == "__main__":
    main()