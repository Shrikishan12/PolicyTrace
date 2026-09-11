CLAIM_SCHEMA = {
    "type": "object",

    "properties": {
        "claims": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {
                    "sentence": {
                        "type": "string"
                    },

                    "actor": {
                        "type": [
                            "string",
                            "null"
                        ]
                    },

                    "action": {
                        "type": "string",
                        "enum": [
                            "collect",
                            "share",
                            "use",
                            "sell",
                            "retain"
                        ]
                    },

                    "polarity": {
                        "type": "string",
                        "enum": [
                            "affirms",
                            "denies"
                        ]
                    },

                    "condition": {
                        "type": [
                            "string",
                            "null"
                        ]
                    },

                    "data_object": {
                        "type": [
                            "string",
                            "null"
                        ]
                    },

                    "entity": {
                        "type": [
                            "string",
                            "null"
                        ]
                    }
                },

                "required": [
                    "sentence",
                    "actor",
                    "action",
                    "polarity",
                    "condition",
                    "data_object",
                    "entity"
                ],

                "additionalProperties": False
            }
        }
    },

    "required": [
        "claims"
    ],

    "additionalProperties": False
}