"""Contract/security coverage without a database; SQL behavior has separate integration tests."""
import json
from uuid import uuid4

import pytest

from test_community_events_api import client, session, FakeResult, FAMILY_ID, USER_ID, POST_ID, NOW

COMMENT_ID = uuid4()


@pytest.fixture(autouse=True)
def reaction_rows(session):
    execute = session.execute

    def query(statement, params=None):
        sql = str(statement)
        if "FROM community.CommentReactions WHERE" in sql:
            return FakeResult([{"Type": "Love", "Total": 2}, {"Type": "Like", "Total": 1}])
        if "LEFT JOIN core.Users AS u" in sql and "community.Comments" in sql:
            return FakeResult([dict(Id=COMMENT_ID, PostId=POST_ID, UserId=USER_ID, AuthorName="Member", Content="Test", CreatedAt=NOW,
                MyReaction="Love", ReactionCount=3, ReactionCounts=json.dumps([{"type":"Love","total":2},{"type":"Like","total":1}]))])
        return execute(statement, params)
    session.execute = query


@pytest.mark.parametrize("kind", ["Like","Love","Haha","Wow","Sad","Angry",None])
def test_comment_reaction_uses_authenticated_actor(client,session,kind):
    response = client.put(f"/api/community/comments/{COMMENT_ID}/reactions",json={"type":kind})
    assert response.status_code == 200
    assert response.json()["type"] == kind
    assert response.json()["reaction_counts"] == {"Love":2,"Like":1}
    assert response.json()["reaction_count"] == 3
    assert session.params_of("usp_SetCommentReaction") == {"id":str(COMMENT_ID),"actor":str(USER_ID),"type":kind}
    assert session.commits == 1


def test_comment_list_contains_summary_and_current_reaction(client):
    response = client.get(f"/api/community/posts/{POST_ID}/comments")
    assert response.status_code == 200
    assert response.json()[0]["my_reaction"] == "Love"
    assert response.json()[0]["reaction_count"] == 3


@pytest.mark.parametrize("payload", [{"type":"bad"},{"type":"Like","user_id":str(uuid4())}])
def test_invalid_or_spoofed_reaction_rejected(client,payload):
    assert client.put(f"/api/community/comments/{COMMENT_ID}/reactions",json=payload).status_code == 422


def test_cross_family_reaction_denied(client,session):
    session.is_member=False
    assert client.put(f"/api/community/comments/{COMMENT_ID}/reactions",json={"type":"Like"}).status_code == 403
    assert session.last_sql("usp_SetCommentReaction") is None


def test_guest_reaction_denied(client,session):
    session.user.role="guest"
    assert client.put(f"/api/community/comments/{COMMENT_ID}/reactions",json={"type":"Like"}).status_code == 403


def test_missing_comment_rejected(client,session):
    session.post_family=None
    assert client.put(f"/api/community/comments/{COMMENT_ID}/reactions",json={"type":"Like"}).status_code == 404


@pytest.mark.parametrize("url", ["javascript:alert(1)","//evil/x","http://example.org/a.jpg","https://user:pass@example.org/a.jpg"])
def test_unsafe_media_rejected(client,url):
    assert client.post("/api/community/posts",json={"family_id":str(FAMILY_ID),"content":"test","media":[{"url":url}]}).status_code==422


def test_local_media_allowed(client):
    assert client.post("/api/community/posts",json={"family_id":str(FAMILY_ID),"content":"test","media":[{"url":"/media/heritage/a.jpg"}]}).status_code==201
