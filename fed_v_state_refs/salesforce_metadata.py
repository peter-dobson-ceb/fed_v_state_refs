import datetime
import json
import re
import urllib.request

salesforce_end_point = r'https://8dni2zb5gl.execute-api.us-west-1.amazonaws.com/' \
                       r'prod/salesforceFetchProductMetadata?typeCode=15'

CACHE_MINUTES = 2  # number of minutes before cache expires


class SalesforceMetadata:
    def __init__(self):
        self._cache_expires = datetime.datetime(2000, 1, 1)
        self._salesforce_metadata_cache = None
        self._salesforce_pub_date_by_id = {}
        self._salesforce_metadata_by_pub_nxt_id = {}

    def get_salesforce_metadata(self):
        if self._cache_expires < datetime.datetime.now():
            with urllib.request.urlopen(salesforce_end_point) as response:
                text = response.read()
            self._salesforce_metadata_cache = json.loads(text)
            self._cache_expires = \
                datetime.datetime.now() + datetime.timedelta(minutes=CACHE_MINUTES)
        return self._salesforce_metadata_cache

    def get_salesforce_metadata_by_pub_nxt_id(self):
        if not len(self._salesforce_metadata_by_pub_nxt_id) or \
                self._cache_expires >= datetime.datetime.now():
            metadata = self.get_salesforce_metadata()
            for product in metadata["products"]:
                nxt_id = product["onlawId"]
                self._salesforce_metadata_by_pub_nxt_id[nxt_id] = product
        return self._salesforce_metadata_by_pub_nxt_id

    def get_salesforce_pub_date_by_id(self):
        if not len(self._salesforce_pub_date_by_id) or \
                self._cache_expires >= datetime.datetime.now():
            metadata = self.get_salesforce_metadata()
            for product in metadata["products"]:
                nxt_id = product["onlawId"]
                pub_date = None
                for edition in product["editions"]:
                    edition_pub_date = datetime.datetime.strptime(edition["publicationDate"],
                                                                  "%Y-%m-%d")
                    if not pub_date or edition_pub_date > pub_date:
                        pub_date = edition_pub_date
                self._salesforce_pub_date_by_id[nxt_id] = pub_date
        return self._salesforce_pub_date_by_id

    def validate(self):
        metadata = self.get_salesforce_metadata()
        for product in metadata["products"]:
            for edition in product['editions']:
                edition_text = edition['edition']
                if re.fullmatch(r"^.*?[0-9]{2}$", edition_text):
                    product_name = product['productName']
                    onlaw_id = product['onlawId']
                    print(f"product '{product_name}' ({onlaw_id}) edition "
                          f"'{edition_text}' has too many digits at the end\n")
        return


salesforce_metadata = SalesforceMetadata()


def get_salesforce_metadata():
    return salesforce_metadata.get_salesforce_metadata()


def get_salesforce_pub_date_by_id():
    return salesforce_metadata.get_salesforce_pub_date_by_id()

# end of file
