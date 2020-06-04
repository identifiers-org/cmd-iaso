import random

from tqdm import tqdm

from xeger import Xeger

XEGER_LIMIT = 10


def generate_scraping_jobs(registry, num_valid, num_random, namespace_ids):
    resources = dict()

    with tqdm(
        total=((num_valid + num_random) * len(registry.resources)),
        desc="Generating LUIs",
    ) as progress:
        generated_luis = 0

        valid_namespace_luis = dict()

        # Collect the namespace-specific information like prefix and LUI pattern
        #  for each resource
        for nid, namespace in registry.namespaces.items():
            if namespace.deprecated is True:
                continue

            valid_namespace_luis[namespace.prefix] = set([namespace.sampleId])

            for resource in namespace.resources:
                if resource.deprecated is True:
                    continue

                rid = resource.id
                url = resource.urlPattern

                resources[rid] = {
                    "prefix": namespace.prefix,
                    "pattern": namespace.pattern,
                    "rid": rid,
                    "url": url,
                    "luis": set([namespace.sampleId, resource.sampleId][:num_valid]),
                }

                valid_namespace_luis[namespace.prefix].add(resource.sampleId)

                generated_luis += len(resources[rid]["luis"])
                progress.update(len(resources[rid]["luis"]))

        if namespace_ids is not None:
            for namespace, luis in namespace_ids.items():
                valid_namespace_luis[namespace] = valid_namespace_luis.get(
                    namespace, set()
                ).union(luis)

        if num_valid > 1:
            # If we need valid LUIs, first attempt to fill them per resource
            for rid, resource in resources.items():
                ids = list(
                    set(
                        lui
                        for lui in namespace_ids.get(resource["prefix"], [])
                        if lui is not None
                    ).difference(resource["luis"])
                )
                random.shuffle(ids)

                pre_len = len(resource["luis"])

                resource["luis"].update(ids[: (num_valid - len(resource["luis"]))])

                generated_luis += len(resource["luis"]) - pre_len
                progress.update(len(resource["luis"]) - pre_len)

            remaining_resources = list(resources.values())

            # Fill up the missing number of total valid LUIs by getting them
            #  from namespaces which have more valid LUIs - if possible
            while len(remaining_resources) > 0 and generated_luis < (
                len(resources) * num_valid
            ):
                resource = remaining_resources.pop(0)

                ids = list(
                    set(
                        lui
                        for lui in namespace_ids.get(resource["prefix"], [])
                        if lui is not None
                    ).difference(resource["luis"])
                )

                # Check if that resource can still contribute valid LUIs
                if len(ids) == 0:
                    continue

                random.shuffle(ids)

                # Attempt to distribute the missing LUIs evenly amongst the
                #  providers which still have valid LUIs
                num_to_add = min(
                    len(ids),
                    (
                        (len(resources) * num_valid)
                        - generated_luis
                        + len(remaining_resources)
                        - 1
                    )
                    // len(remaining_resources),
                )

                resource["luis"].update(ids[:num_to_add])

                generated_luis += num_to_add
                progress.update(num_to_add)

                remaining_resources.append(resource)

        if num_random > 0:
            # If we need random LUIs, generate them from the namespace's
            #  LUI regex pattern
            for rid, resource in resources.items():
                luis = resource["luis"]
                start_len = len(luis)

                pattern = resource["pattern"].replace("\\\\", "\\")

                xeg = Xeger(limit=XEGER_LIMIT)

                security = 0

                # Generate new random LUIs but break if we need more than num_random * 10 attempts
                while (len(luis) < (start_len + num_random)) and (
                    security < num_random * 10
                ):
                    lui = xeg.xeger(pattern)

                    if lui is not None:
                        pre_len = len(luis)
                        luis.add(lui)
                        post_len = len(luis)

                        generated_luis += post_len - pre_len
                        progress.update(post_len - pre_len)

                    security += 1

    jobs = []

    with tqdm(total=generated_luis, desc="Generating Jobs") as progress:
        # Generate the jobs from the LUIs
        for rid, resource in resources.items():
            resource["luis"] = list(resource["luis"])

            valid_luis = valid_namespace_luis[resource["prefix"]]

            for lui in resource["luis"]:
                jobs.append(
                    (
                        rid,
                        lui,
                        lui not in valid_luis,
                        resource["url"].replace("{$id}", lui),
                    )
                )

                progress.update(1)

    random.shuffle(jobs)

    return jobs
