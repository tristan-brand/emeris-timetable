from uni_scheduler.event import Event


def test_gen_source_id_is_deterministic_for_same_event_data():
    event = Event(
        title="Math 101",
        location="Room A",
        day="Monday",
        date="1 Jan",
        start_time="9H00",
        end_time="10H00",
    )

    first = event.gen_source_id()
    second = event.gen_source_id()

    assert first == second


def test_gen_source_id_changes_when_source_fields_change():
    base = Event("Math 101", "Room A", "Monday", "1 Jan", "9H00", "10H00")
    different_title = Event("Physics 101", "Room A", "Monday", "1 Jan", "9H00", "10H00")
    different_date = Event("Math 101", "Room A", "Monday", "2 Jan", "9H00", "10H00")
    different_start = Event("Math 101", "Room A", "Monday", "1 Jan", "10H00", "11H00")

    assert base.gen_source_id() != different_title.gen_source_id()
    assert base.gen_source_id() != different_date.gen_source_id()
    assert base.gen_source_id() != different_start.gen_source_id()


def test_gen_source_id_has_expected_format():
    event = Event("Math 101", "Room A", "Monday", "1 Jan", "9H00", "10H00")

    source_id = event.gen_source_id()

    assert len(source_id) == 20
    assert all(ch in "0123456789abcdef" for ch in source_id)


def test_to_google_event_embeds_same_source_id():
    event = Event("Math 101", "Room A", "Monday", "1 Jan", "9H00", "10H00")

    payload = event.to_google_event(year=2026)

    assert payload["extendedProperties"]["private"]["source_id"] == event.gen_source_id()
