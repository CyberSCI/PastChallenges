#ifndef UTILS_H
#define UTILS_H

#include <QString>

enum Candidate {
    EstebanDeSouza = 0,
    AriusPerez,
    RaphaelVelasquez,
    GenRamonEsperanza,
    JoelPlata,
    SofiaDaSilva,
    AnaPaulaEspinoza,
    VeraGomes,
    XavierGonzalez,
    PedroGaleano,
    NumCandidates
};

enum Region {
    Verdantia = 0,
    Elarion,
    Zepharion,
    Valtara,
    Eryndor,
    NumRegions
};

QString getCandidateName(Candidate candidate);

std::optional<double> getRegionVoters(Region region);

bool submitVotes(Region region, const QVector<int>& votesPerCandidate);

#endif  // UTILS_H
