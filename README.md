# Pretty Print Word Definitions From The M-W JSON API

This small project uses the JSON API for Merriam-Webster's Collegiate® Dictionary with Audio: https://dictionaryapi.com/products/api-collegiate-dictionary.

The goal is to pretty print the returned JSON result closer to what's shown on the Merriam-Webster website. I plan to integrate this project into an Anki add-on that automatically generates word explanations by looking up via the Merriam-Webster dictionary JSON API.

## Testing

Make sure to have API key stored in `config.json` file:

```json
{
    "api_key": "YOUR_MW_DICTIONARY_API_KEY"
}
```

Run shell command to print result for the word to look up:

```bash
$ python define.py monitor
```
