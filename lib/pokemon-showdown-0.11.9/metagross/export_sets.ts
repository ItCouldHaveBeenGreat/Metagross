import Dex from '../sim/dex';
import { RandomTeams } from '../data/random-teams';
import * as fs from 'fs';
import * as path from 'path';
import { DexFormats } from '../sim/dex-formats';


interface PokemonSet {
    shiny: boolean;
    moves: string[];
    evs: { [key: string]: number };
    ivs: { [key: string]: number };
    role: string;
    ability: string;
    item: string;
    name: string;
    species: string;
    gender: string;
    level: number;
    teraType: string;
}

function generatePokemonSets() {
    const gen9RandomSets = require('../data/random-sets.json');
    const pokemonSets: { [key: string]: PokemonSet } = {};

    // Create a list of Pokemon names we need to populate
    const pokemonToPopulate = Object.keys(gen9RandomSets);

    // Initialize RandomTeams with Gen 9 format retrieved via get method
    Dex.loadData()
    const dexFormats = new DexFormats(Dex);
    console.log("--FORMATS--")
    console.log(dexFormats)
    console.log("--FORMATS LIST--")
    console.log(dexFormats.all())
    const gen9Format = dexFormats.get('gen9randombattle');
    console.log("--GEN9--")
    console.log(gen9Format)
    const randomTeams = new RandomTeams(gen9Format.id, null);

    // Keep track of how many Pokemon we've populated
    let populatedCount = 0;
    let attempts = 0;
    const maxAttempts = 100; // Safety limit to prevent infinite loops

    // Continue generating teams until we've populated all Pokemon or hit the max attempts
    while (populatedCount < pokemonToPopulate.length && attempts < maxAttempts) {
        attempts++;

        // Generate a random team
        const randomTeam = randomTeams.randomTeam();

        // Process each Pokemon in the team
        for (const set of randomTeam) {
            const speciesName = set.species.toLowerCase();

            // Check if this Pokemon is in our list and not already populated
            if (pokemonToPopulate.includes(speciesName) && !pokemonSets[speciesName]) {
                // Add this Pokemon to our sets
                pokemonSets[speciesName] = {
                    shiny: set.shiny,
                    moves: set.moves,
                    evs: set.evs,
                    ivs: set.ivs,
                    role: set.role || '',
                    ability: set.ability,
                    item: set.item,
                    name: set.name,
                    species: set.species,
                    gender: set.gender,
                    level: set.level,
                    teraType: set.teraType || '',
                };

                // Increment our counter
                populatedCount++;

                // If we've populated all Pokemon, we can break out
                if (populatedCount >= pokemonToPopulate.length) {
                    break;
                }
            }
        }

        console.log(`Generated team ${attempts}, populated ${populatedCount}/${pokemonToPopulate.length} Pokemon`);
    }

    // Check if we've populated all Pokemon
    if (populatedCount < pokemonToPopulate.length) {
        console.warn(`Warning: Only populated ${populatedCount}/${pokemonToPopulate.length} Pokemon after ${attempts} attempts`);
    }

    // Write the results to a file
    const outputPath = path.join(__dirname, 'generated-pokemon-sets.json');
    fs.writeFileSync(outputPath, JSON.stringify(pokemonSets, null, 2));
    console.log(`Wrote ${Object.keys(pokemonSets).length} Pokemon sets to ${outputPath}`);
}

generatePokemonSets();