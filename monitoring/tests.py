from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Device, Measurement

User = get_user_model()


class MeanExample(SimpleTestCase):
    def test_expected_mean(self):
        values = [Decimal("20.00"), Decimal("30.00")]
        self.assertEqual(sum(values) / len(values), Decimal("25.00"))


class MonitoringIntegrationTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="user_a", password="pass_a_123")
        self.user_b = User.objects.create_user(username="user_b", password="pass_b_123")

        self.dev_a = Device.objects.create(
            name="Компост центр", serial="CMP-19-01", owner=self.user_a
        )
        self.dev_null = Device.objects.create(
            name="Двір", serial="CMP-19-03", owner=None
        )
        self.url_create = reverse("monitoring:measurement_create")

    def test_anonymous_redirect_to_login(self):
        resp = self.client.get(self.url_create)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)

    def test_get_shows_only_own_devices(self):
        self.client.force_login(self.user_a)
        resp = self.client.get(self.url_create)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.dev_a.serial)
        self.assertNotContains(resp, self.dev_null.serial)

    def test_two_users_ownership_and_null_owner(self):
        now_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        # 1. Власник A успішно додає вимірювання
        self.client.force_login(self.user_a)
        resp_ok = self.client.post(
            self.url_create,
            {"device": self.dev_a.pk, "temperature": "62.50", "measured_at": now_str},
        )
        self.assertRedirects(
            resp_ok, reverse("monitoring:detail", kwargs={"pk": self.dev_a.pk})
        )
        self.assertEqual(Measurement.objects.count(), 1)

        # 2. Користувач B намагається додати вимірювання до пристрою A
        self.client.force_login(self.user_b)
        resp_b = self.client.post(
            self.url_create,
            {"device": self.dev_a.pk, "temperature": "65.00", "measured_at": now_str},
        )
        self.assertEqual(resp_b.status_code, 200)
        self.assertFormError(
            resp_b.context["form"],
            "device",
            "Select a valid choice. That choice is not one of the available choices.",
        )
        self.assertEqual(Measurement.objects.count(), 1)

        # 3. Нічийний пристрій (owner=NULL) відхиляється
        resp_null = self.client.post(
            self.url_create,
            {
                "device": self.dev_null.pk,
                "temperature": "50.00",
                "measured_at": now_str,
            },
        )
        self.assertEqual(resp_null.status_code, 200)
        self.assertEqual(Measurement.objects.count(), 1)

    def test_empty_bound_post(self):
        self.client.force_login(self.user_a)
        resp = self.client.post(self.url_create, {})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertTrue(form.is_bound)
        self.assertIn("device", form.errors)
        self.assertIn("temperature", form.errors)

    def test_csrf_enforced(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user_a)
        now_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        # Без CSRF-токена -> 403
        resp_no_csrf = csrf_client.post(
            self.url_create,
            {"device": self.dev_a.pk, "temperature": "60.00", "measured_at": now_str},
        )
        self.assertEqual(resp_no_csrf.status_code, 403)

    def test_temperature_boundaries_and_invalid(self):
        self.client.force_login(self.user_a)
        now_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        for temp in ("-80.00", "150.00"):
            resp = self.client.post(
                self.url_create,
                {"device": self.dev_a.pk, "temperature": temp, "measured_at": now_str},
            )
            self.assertEqual(resp.status_code, 302)
        self.assertEqual(Measurement.objects.count(), 2)

        # Поза межами (151 °C) -> 200 з помилкою, без запису
        resp_bad = self.client.post(
            self.url_create,
            {"device": self.dev_a.pk, "temperature": "151.00", "measured_at": now_str},
        )
        self.assertEqual(resp_bad.status_code, 200)
        self.assertEqual(Measurement.objects.count(), 2)

    def test_put_method_not_allowed(self):
        self.client.force_login(self.user_a)
        resp = self.client.put(self.url_create)
        self.assertEqual(resp.status_code, 405)

    def test_detail_ordering_and_empty_device(self):
        t_old = timezone.now() - timedelta(hours=2)
        t_new = timezone.now() - timedelta(minutes=5)
        Measurement.objects.create(
            device=self.dev_a, temperature=Decimal("55.00"), measured_at=t_old
        )
        Measurement.objects.create(
            device=self.dev_a, temperature=Decimal("61.00"), measured_at=t_new
        )

        resp = self.client.get(
            reverse("monitoring:detail", kwargs={"pk": self.dev_a.pk})
        )
        self.assertEqual(resp.status_code, 200)
        meas_list = list(resp.context["measurements"])
        self.assertEqual(meas_list[0].temperature, Decimal("61.00"))

        resp_empty = self.client.get(
            reverse("monitoring:detail", kwargs={"pk": self.dev_null.pk})
        )
        self.assertContains(resp_empty, "Вимірювань немає")

    def test_extra_criterion_future_time_rejected(self):
        self.client.force_login(self.user_a)
        future_str = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        resp = self.client.post(
            self.url_create,
            {
                "device": self.dev_a.pk,
                "temperature": "58.00",
                "measured_at": future_str,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("measured_at", resp.context["form"].errors)
        self.assertEqual(Measurement.objects.count(), 0)
