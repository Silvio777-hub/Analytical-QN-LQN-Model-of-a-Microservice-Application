## Table 5 — Visit Ratio, Service Time, Demand, CPU Load @ 10 req/s

| Microservice | V_i | S_i (ms) | D_i (ms) | ρ @ 10 req/s | N_i | Rank |
|---|---:|---:|---:|---:|---:|---:|
| Frontend | 1.0000 | 18.880 | 18.880 | 18.88% | 0.2327 | 1 |
| CartService | 0.0399 | 35.229 | 1.406 | 1.41% | 0.0143 | 2 |
| CheckoutService | 0.0367 | 33.522 | 1.230 | 1.23% | 0.0125 | 3 |
| CurrencyService | 0.2771 | 1.603 | 0.444 | 0.44% | 0.0045 | 4 |
| AdService | 0.0218 | 19.882 | 0.433 | 0.43% | 0.0044 | 5 |
| RecommendationService | 0.0898 | 3.828 | 0.344 | 0.34% | 0.0034 | 6 |
| PaymentService | 0.0051 | 47.942 | 0.244 | 0.24% | 0.0024 | 7 |
| ProductCatalogService | 0.6369 | 0.324 | 0.206 | 0.21% | 0.0021 | 8 |
| ShippingService | 0.0142 | 13.445 | 0.191 | 0.19% | 0.0019 | 9 |
| Redis | 0.0379 | 2.000 | 0.076 | 0.08% | 0.0008 | 10 |
| EmailService | 0.0051 | 1.293 | 0.007 | 0.01% | 0.0001 | 11 |

## Table 6 — Service Time Breakdown (Mean, Median, P95, P99)

| Microservice | Mean | Median | P95 | P99 | CoV | Samples | Source |
|---|---:|---:|---:|---:|---:|---:|---|
| AdService | 19.882 | 6.656 | 92.453 | 111.587 | 1.424 | 79 | empirical — Docker Jaeger live run (6,642 spans) |
| CartService | 35.229 | 10.427 | 148.572 | 278.698 | 1.946 | 221 | empirical — Docker Jaeger live run (6,642 spans) |
| CheckoutService | 33.522 | 6.247 | 141.009 | 403.764 | 2.800 | 992 | empirical — Docker Jaeger live run (6,642 spans) |
| CurrencyService | 1.603 | 0.284 | 8.781 | 28.194 | 4.381 | 564 | empirical — Docker Jaeger live run (6,642 spans) |
| EmailService | 1.293 | 0.397 | 5.256 | 12.434 | 3.073 | 95 | empirical — Docker Jaeger live run (6,642 spans) |
| Frontend | 18.880 | 1.745 | 44.722 | 175.605 | 19.054 | 2386 | empirical — Docker Jaeger live run (6,642 spans) |
| PaymentService | 47.942 | 1.518 | 88.334 | 1537.177 | 4.808 | 96 | empirical — Docker Jaeger live run (6,642 spans) |
| ProductCatalogService | 0.324 | 0.015 | 0.045 | 1.704 | 29.442 | 1574 | empirical — Docker Jaeger live run (6,642 spans) |
| RecommendationService | 3.828 | 1.256 | 11.476 | 38.704 | 6.430 | 404 | empirical — Docker Jaeger live run (6,642 spans) |
| ShippingService | 13.445 | 1.562 | 38.203 | 217.130 | 3.893 | 131 | empirical — Docker Jaeger live run (6,642 spans) |
| Redis | 2.000 | 1.800 | 3.800 | 5.500 | 0.300 | 500 | default — not measured (Redis state store) |

## Table 7 — Model vs. Observed Response Times

| λ (req/s) | Observed RT (ms) | Model Pred (ms) | Error (%) |
|---:|---:|---:|---:|
| 2.0 | 354.2 | 101.50 | 71.34% |
| 5.0 | 996.8 | 139.62 | 85.99% |
| 8.0 | 857.0 | 228.54 | 73.33% |
| 10.0 | 2887.9 | 406.33 | 85.93% |

## Table 8 — M/M/c Scaling (Bottleneck Service)

Bottleneck service: Frontend, S₀ = 18.88 ms
Single-replica capacity X₁ = 52.97 req/s

| c | Max Capacity (req/s) | Latency @ 10 req/s | Capacity Gain | USL Efficiency |
|---:|---:|---:|---:|---:|
| 1 | 52.97 | 23.27 | 1.00× | 100.0% |
| 2 | 102.75 | 19.05 | 1.94× | 97.0% |
| 3 | 148.75 | 18.89 | 2.81× | 93.6% |
| 4 | 190.59 | 18.88 | 3.60× | 90.0% |
| 5 | 228.06 | 18.88 | 4.31× | 86.1% |
| 6 | 261.13 | 18.88 | 4.93× | 82.2% |

## Table 9 — Sensitivity & ROI

| Microservice | V_i | ρ @ 10 | Sensitivity | ROI Share |
|---|---:|---:|---:|---:|
| Frontend | 1.0000 | 18.88% | 1.5197 | 56.44% |
| ProductCatalogService | 0.6369 | 0.21% | 0.6396 | 23.76% |
| CurrencyService | 0.2771 | 0.44% | 0.2796 | 10.39% |
| RecommendationService | 0.0898 | 0.34% | 0.0904 | 3.36% |
| CartService | 0.0399 | 1.41% | 0.0411 | 1.52% |
| Redis | 0.0379 | 0.08% | 0.0380 | 1.41% |
| CheckoutService | 0.0367 | 1.23% | 0.0376 | 1.40% |
| AdService | 0.0218 | 0.43% | 0.0220 | 0.82% |
| ShippingService | 0.0142 | 0.19% | 0.0143 | 0.53% |
| PaymentService | 0.0051 | 0.24% | 0.0051 | 0.19% |
| EmailService | 0.0051 | 0.01% | 0.0051 | 0.19% |

## Metadata
- Total services: 11
- Total samples: 7042
- Mean timeout rate: 4.55%
- Bottleneck: Frontend