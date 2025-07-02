#include "utils.h"

#include <QDebug>
#include <QMap>

#include <VMProtectSDK.h>

QString getCandidateName(Candidate candidate) {
    const QMap<Candidate, QString> candidateMap = {
        {EstebanDeSouza, "Esteban de Souza"},
        {AriusPerez, "Arius Perez"},
        {RaphaelVelasquez, "Raphael Velasquez"},
        {GenRamonEsperanza, "Gen. Ramon Esperanza"},
        {JoelPlata, "Joel Plata"},
        {SofiaDaSilva, "Sofia da Silva"},
        {AnaPaulaEspinoza, "Ana Paula Espinoza"},
        {VeraGomes, "Vera Gomes"},
        {XavierGonzalez, "Xavier Gonzalez"},
        {PedroGaleano, "Pedro Galeano"}
    };

    return candidateMap.value(candidate, "Unknown");
}

// Get the number of voters in each region
std::optional<double> getRegionVoters(Region region) {
    // Check for debuggers
    if (VMProtectIsDebuggerPresent(true) || !VMProtectIsValidImageCRC()) {
        return std::nullopt;
    }

    // We're defining a new variable here instead of returning from each case
    // so this swith statement gets optimized to array indexing
    double voters;
    switch (region) {
        case Verdantia:
            voters = 12125863;
            break;
        case Elarion:
            return 3456789;
            break;
        case Zepharion:
            return 8765432;
            break;
        case Valtara:
            return 10234567;
            break;
        case Eryndor:
            return 1543210;
            break;
        case NumRegions:
        default:
            voters = -1;
            break;
    }

    return voters;
}
