import {writeFileSync} from 'fs';

import {Moves} from '../data/moves';

// Convert the MOVES object to a JSON string
const movesJson: string = JSON.stringify(Moves, null, 2);

// Function to export the JSON string to a file
function exportToJsonFile(jsonString: string, filename: string) {
  const blob = new Blob([jsonString], {type: "application/json"});
  writeFileSync(filename, movesJson);
}

// Export the MOVES object as a JSON file
exportToJsonFile(movesJson, "moves_export.json");