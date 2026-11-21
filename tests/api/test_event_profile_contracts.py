from datetime import datetime
from uuid import uuid4
import pytest
from pydantic import ValidationError
from test_community_events_api import client,session


def test_event_end_round_trip_utc():
    from app.domains.events.schemas import EventCreateRequest
    model=EventCreateRequest(family_id=uuid4(),title="Event",location="City",event_date="2030-01-01T10:00:00+07:00",end_date="2030-01-01T11:00:00+07:00")
    assert model.event_date==datetime(2030,1,1,3)
    assert model.end_date==datetime(2030,1,1,4)


@pytest.mark.parametrize("end",["2030-01-01T09:00:00Z","2030-01-01T10:00:00Z"])
def test_end_must_follow_start(end):
    from app.domains.events.schemas import EventCreateRequest
    with pytest.raises(ValidationError):EventCreateRequest(family_id=uuid4(),title="Event",location="City",event_date="2030-01-01T10:00:00Z",end_date=end)


@pytest.mark.parametrize("field",["institution","degree","company","position"])
def test_history_blank_strings_rejected(field):
    from app.domains.directory.router import HistoryFields
    with pytest.raises(ValidationError):HistoryFields(start_date="2020-01-01",**{field:"   "})


@pytest.mark.parametrize("resource,body",[("educations",{"institution":"School"}),("work",{"company":"Company"})])
def test_required_history_cannot_bypass_api(client,session,resource,body):
    response=client.post(f"/api/directory/{uuid4()}/{resource}",json={**body,"start_date":"2020-01-01"})
    assert response.status_code==422
    assert session.last_sql("usp_ManageHistory") is None
