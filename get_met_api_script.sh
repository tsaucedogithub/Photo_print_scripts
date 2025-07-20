#!/usr/bin/env bash
shopt -s expand_aliases

ARTIST="${1:-Rothko}"
SEARCH_URL="https://collectionapi.metmuseum.org/public/collection/v1/search?artistOrCulture=true&q=${ARTIST}&hasImages=true"

# 1) Fetch search response and check for results
echo "Searching for artist: $ARTIST"
echo "Using URL: $SEARCH_URL"
if ! command -v jq >/dev/null; then
  echo "Error: jq is not installed." >&2
  exit 1
fi
RESPONSE=$(curl -s "$SEARCH_URL")
TOTAL=$(echo "$RESPONSE" | jq -r '.total')
if [ "$TOTAL" -eq 0 ]; then
  echo "No open-access images found for artist: $ARTIST"
  exit 1
fi
echo "$RESPONSE" | jq -r '.objectIDs[]' | gshuf -n5 > ids.txt

# 2) Loop over each ID to download its high-res image
while IFS= read -r id; do
  img=$(curl -s "https://collectionapi.metmuseum.org/public/collection/v1/objects/$id" \
        | jq -r '.primaryImage')
  [[ -n "$img" ]] && curl -sL -o ~/Downloads/"${id}.jpg" "$img"
done < ids.txt