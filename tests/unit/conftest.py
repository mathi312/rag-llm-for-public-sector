import sys
from unittest.mock import MagicMock, patch


# Patch PocketBase and os.getenv BEFORE the module is ever imported.
# This prevents the top-level CLIENT = PocketBase(...) and
# auth_with_password(...) from making real network calls during collection.

mock_pb_instance = MagicMock()

# Stub out the entire pocketbase package so the import doesn't fail
# even if the library isn't installed in the test environment.

sys.modules.setdefault("pocketbase", MagicMock())
sys.modules["pocketbase.client"] = MagicMock()


pb_patch = patch(

    "extensions.documents.documentupload.PocketBase",
    return_value=mock_pb_instance,

)

env_patch = patch.dict(

 "os.environ",

 {

 "POCKETBASE_URL": "http://fake-url",
 "POCKETBASE_ADMIN_USERNAME": "admin",
 "POCKETBASE_ADMIN_PASSWORD": "password",

},

)




env_patch.start()

pb_patch.start()