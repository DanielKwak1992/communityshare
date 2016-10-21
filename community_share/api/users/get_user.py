from typing import Optional

from flask import jsonify, request, Response

from community_share import Store, with_store
from community_share.app_exceptions import NotFound
from community_share.flask_helpers import needs_auth, serialize
from community_share.models.user import User
from community_share.utils import int_or


@needs_auth()
def endpoint(user_id: int, requester: User) -> Response:
    """ User Endpoint

    http:get:: /rest/users/<user_id:int>

    **Example request**:

    .. sourcecode:: http

       GET /rest/users/42?field=name&field=bio HTTP/1.1
       Host: app.communityshare.us
       Accept: application/json
       Authorization: Basic:username:password

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
          "user": {
             "id": 23,
             "name": "Bob Smith",
             "bio": "On the weekends I polish copper mines."
          },
          "links": [ {
             "rel": "self",
             "href": "https://app.communityshare.us/rest/users/42"
          }
       }

    :query int user_id: id of user to fetch
    :query list string field: additional fields to return, always returns user id, default returns all fields

    :statuscode 200: user successfully fetched
    :statuscode 400: invalid arguments passed in
    :statuscode 401: needs authentication

    """
    user_id = int_or(user_id, None)
    fields = request.args.getlist('field')
    fields = fields if fields else None
    user = serialize(requester, get_user(user_id), fields=fields)

    # if the requester is not authorized
    # to see a user, it should be opaque
    # whether or not the user even exists
    # in this case, we return a "not found"
    # for both cases
    if user is None:
        raise NotFound()

    return jsonify({
        'user': {
            **user,
            'links': [{
                'rel': 'self',
                'href': request.url,
            }]
        }
    })


@with_store
def get_user(user_id: int, store: Store=None) -> Optional[User]:
    return store.session.query(User).get(user_id)
