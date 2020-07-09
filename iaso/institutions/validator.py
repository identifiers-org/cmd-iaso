class InstitutionsValidator:
    @staticmethod
    def check_and_create(difference):
        return InstitutionsValidator(difference)

    def __init__(self, difference):
        self.difference = difference

    @staticmethod
    def format_lui_link(url, lui):
        return url.replace(lui, "{$id}") if lui in url else f"<{url}>"

    def format(self, formatter):
        formatter.format_json(
            "Institution Difference", self.difference, 3,
        )
