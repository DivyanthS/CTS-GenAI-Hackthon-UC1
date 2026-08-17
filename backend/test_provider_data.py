from services.provider_data import ProviderDataService


service = ProviderDataService().load()

print("Providers loaded:", service.provider_count)

assert service.provider_count == 5410

provider_id = "PRV51459"

assert service.provider_exists(provider_id)

features = service.get_provider_features(provider_id)

print("Provider:", provider_id)
print("Feature count:", len(features))
print("First features:", list(features.items())[:5])

assert len(features) == 30

print("\nProvider data service test PASSED")