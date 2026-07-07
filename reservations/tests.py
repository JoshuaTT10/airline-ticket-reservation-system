def test_django_settings_are_loaded(settings):
    assert settings.ROOT_URLCONF == "airline_reservation.urls"
