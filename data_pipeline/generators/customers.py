"""Customer data generator — realistic customer profiles."""

import random

import pandas as pd
from faker import Faker

from data_pipeline.generators.base import GenerationConfig


def generate_customers(config: GenerationConfig | None = None) -> pd.DataFrame:
    """Generate customer records with realistic distributions.

    Includes intentional data quality issues:
    - ~2% NULL values in optional fields (phone, signup_date)
    - ~0.5% duplicate emails (data quality edge case)
    """
    if config is None:
        from data_pipeline.generators.base import DEFAULT_CONFIG
        config = DEFAULT_CONFIG

    fake = Faker()
    Faker.seed(config.random_seed)
    random.seed(config.random_seed)

    # Customer segments with weighted distribution
    segments = ["Premium", "Regular", "Budget", "Enterprise"]
    segment_weights = [0.15, 0.50, 0.25, 0.10]

    customers = []
    used_emails = set()

    for i in range(1, config.num_customers + 1):
        # Generate unique email (with intentional duplicates for quality testing)
        if random.random() < config.duplicate_rate and len(used_emails) > 10:
            email = random.choice(list(used_emails))
        else:
            email = f"customer{i}_{fake.user_name()}@{fake.free_email_domain()}"
            used_emails.add(email)

        # Region assignment (weighted — more customers in larger regions)
        region_weights = [0.30, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
        region_id = random.choices(range(1, config.num_regions + 1), weights=region_weights, k=1)[0]

        # Signup date (more recent customers)
        signup_date = fake.date_between(start_date="-3y", end_date="today")

        # Intentional NULLs in optional fields
        phone = fake.phone_number() if random.random() > config.null_rate else None

        customer = {
            "customer_id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": email,
            "phone": phone,
            "region_id": region_id,
            "signup_date": signup_date,
            "segment": random.choices(segments, weights=segment_weights, k=1)[0],
        }
        customers.append(customer)

    df = pd.DataFrame(customers)
    return df
