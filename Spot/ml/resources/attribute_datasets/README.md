Learner Attributes datasets
---------------------------

The structure of this directory should look like this:

```
- .
  - tag-name-1
    - Attribute-Name-1.json
    - Attribute-Name-2.json
  - tag-name-2
    - Attribute-Name-1.json
```

The format of a dataset JSON file is:

```javascript
{
	"description": "what does this attribute do", // Optional
	"value_range": ["label1", "label2", ..., "labeln"],
	"data": [
		["Preprocessed sample text", [flags], "labelx"],
		...
	]
}
```
