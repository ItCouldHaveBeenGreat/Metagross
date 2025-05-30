

### Exporting Datasets
NOTE: The current process sucks
```
cd lib/pokemon-showdown-0.11.9
npm run build
tsc metagross/export_moves.ts  # this will fail
node metagross/export_moves.js
mv moves_export.json ../../metagross/export/

tsc metagross/export_sets.ts 
```