from collections import namedtuple


def _create_namedtuple_from_dict(key, dict):
    return namedtuple(key, dict.keys())


def _create_convert_namedtuple_from_dict(key, dict):
    return _create_namedtuple_from_dict(key, dict)(**dict)


def _field_to_class_name(field):
    classname = field

    if len(classname) > 0:
        classname = classname[0].upper() + classname[1:]

    if classname.endswith("s"):
        classname = classname[:-1]

    return classname


def json_to_any_db(
    data,
    default=lambda: None,
    append=lambda store, key, value: None,
    find=lambda store, key: None,
    dbname=None,
):
    db = dict()
    classes = dict()

    def _explore_recurse(field, data, db, classes):
        if type(data) == list:
            if field not in db:
                db[field] = default()

            return [_explore_recurse(field, item, db, classes) for item in data]

        if type(data) == dict:
            if field not in db:
                db[field] = default()

            if field not in classes:
                classes[field] = _create_namedtuple_from_dict(
                    _field_to_class_name(field), data
                )

            primary_key = data[next(iter(data))]

            item = find(db[field], primary_key)

            if item is None:
                item = classes[field](
                    *[
                        _explore_recurse(key, value, db, classes)
                        for key, value in data.items()
                    ]
                )

                append(db[field], primary_key, item)

            return item

        return data

    for key, value in data.items():
        _explore_recurse(key, value, db, classes)

    return _create_convert_namedtuple_from_dict(
        "JSONDB" if dbname is None else dbname, db
    )


def json_to_dict_db(data, dbname=None):
    return json_to_any_db(
        data,
        default=lambda: dict(),
        append=lambda store, key, value: store.update({key: value}),
        find=lambda store, key: store.get(key, None),
        dbname=dbname,
    )


def json_to_list_db(data, dbname=None):
    return json_to_any_db(
        data,
        default=lambda: [],
        append=lambda store, key, value: store.append(value),
        find=lambda store, key: next(
            (item for item in store if item[next(iter(item))] == key), None
        ),
        dbname=dbname,
    )


def json_to_namedtuple(data, ntname=None):
    classes = dict()

    def _explore_recurse(field, data, classes):
        if type(data) == list:
            return [_explore_recurse(field, item, classes) for item in data]

        if type(data) == dict:
            if field not in classes:
                classes[field] = _create_namedtuple_from_dict(
                    _field_to_class_name(field), data
                )

            primary_key = data[next(iter(data))]

            fields = {
                key: _explore_recurse(key, value, classes)
                for key, value in data.items()
            }

            item = classes[field](
                *[fields[fieldname] for fieldname in classes[field]._fields]
            )

            return item

        return data

    return _explore_recurse("JSONNT" if ntname is None else ntname, data, classes)
