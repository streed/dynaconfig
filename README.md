# dynaconfig
Centralized Configuration Service

Configuration is hard so make it somewhat easier by adding a layer of abstraction into your stack.

# What?

This provides a simple restful interface to create and update configurations.

# How?

A simple flask server running in your favorite wsgi container for the connections and a RethinkDB database in the backend.

# Cool?

Very cool. We currently provide the creation of configuration files based on some `user_id` and some `config_name`. These configs contain the values as well as a simple audit trail that can be used to follow changes throughout a configurations life time.

# Exmaples

Input:
```bash
curl -XPOST http://localhost:5000/values/1/test -d'{"test": 1}' -H "Content-Type: application/json"
```

Output:
```json
{
    "audit_trail": [
        {
            "changes": [
                {
                    "action": "added",
                    "key": "test",
                    "value": 1
                }
            ],
            "created_at": "Sun Mar 08 2015 05:41:10 GMT+00:00",
            "version": 1
        }
    ],
    "config_id": "1-test",
    "id": "c51b1c98-5d1c-4657-86d2-ca19020192aa",
    "values": {
        "test": 1
    },
    "version": 1
}
```

As you can see there is a lot of information. But, the simple is every config is versioned, contains an audit trail, as well as the latest configuration values. Now, let's remove the `test` value and add a `hello` value.

Intput:
```bash
curl -XPOST http://localhost:5000/values/1/test -d'{"hello": "world"}' -H "Content-Type: application/json"
```

Output:
```json
{
    "audit_trail": [
        {
            "changes": [
                {
                    "action": "added",
                    "key": "test"
                }
            ],
            "created_at": "Sun Mar 08 2015 05:41:10 GMT+00:00",
            "version": 1
        },
        {
            "changes": [
                {
                    "action": "removed",
                    "key": "test",
                    "value": 1
                },
                {
                    "action": "added",
                    "key": "hello",
                    "value": "world"
                }
            ],
            "created_at": "Sun Mar 08 2015 05:46:14 GMT+00:00",
            "version": 1
        }
    ],
    "config_id": "1-test",
    "id": "c51b1c98-5d1c-4657-86d2-ca19020192aa",
    "values": {
        "hello": "world"
    },
    "version": 1
}
```

As you can see the audit log was updated with the changes and the values reflect the updated configuration.
