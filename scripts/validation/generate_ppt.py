from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt


def create_presentation():
    prs = Presentation()

    # Slide 1: Title
    slide_layout = prs.slide_layouts[0]  # Title slide
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    title.text = "Performance Modelling of a Microservice Application"
    subtitle.text = "Analytical Queueing Network Formulation and Validation\nGoogle Online Boutique Benchmark\nBy Essa Janneh & Opoka JM Silvio\nMay 2026"

    # Slide 2: Core Objectives
    slide_layout = prs.slide_layouts[1]  # Title and Content
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Core Objectives"

    content = slide.placeholders[1].text_frame
    content.text = (
        "Bridge the gap between queueing theory and real-world cloud deployments."
    )
    p = content.add_paragraph()
    p.text = "Deploy the 11-service Google Online Boutique in a controlled containerized environment."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Empirically collect telemetry (Prometheus/Jaeger) to derive service demands and routing probabilities."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Model the topology as an Open Queueing Network (M/M/1 & M/M/c) via Mean Value Analysis (MVA)."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Validate predictions against empirical tail latencies and Little's Law."
    p.level = 1

    # Slide 3: Target Architecture
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Target System Architecture"

    content = slide.placeholders[1].text_frame
    content.text = "Google Online Boutique Application"
    p = content.add_paragraph()
    p.text = "Polyglot microservices (Go, C#, Node.js, Python, Java)."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Communication via gRPC over HTTP/2 using Protocol Buffers."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Frontend acts as an API gateway (scatter-gather pattern)."
    p.level = 1
    p = content.add_paragraph()
    p.text = "CartService persists to an in-memory Redis store, eliminating highly variable disk I/O latency."
    p.level = 1

    # Slide 4: Data Extraction & Tracing
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Empirical Telemetry & Parameter Extraction"

    content = slide.placeholders[1].text_frame
    content.text = (
        "Extracted data from 15,000 steady-state distributed traces via Jaeger."
    )
    p = content.add_paragraph()
    p.text = "Transition Routing Matrix (P): Mapped parent-child gRPC calls."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Exclusive Service Demand (Si): Extracted CPU execution time."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Engineered an Interval-Merging sweep-line algorithm (O(N log N))."
    p.level = 2
    p = content.add_paragraph()
    p.text = "Prevented double-counting of parallel fan-outs, correcting Frontend demand to 80.00 ms."
    p.level = 2

    # Slide 5: Queueing Network Formulation
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Queueing Network Formulation (MVA)"

    content = slide.placeholders[1].text_frame
    content.text = "Modeled as an Open Queueing Network (Jackson Network)."
    p = content.add_paragraph()
    p.text = "External arrival rate λ = 10.0 req/s (Markovian)."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Traffic Equations: Computed internal arrival rates (λ_i) and visit ratios (V_i) from routing matrix."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Mean Value Analysis (MVA): Pollaczek-Khinchine approximations used to compute Utilization (ρ), Mean Response Time (R), and Concurrency (N)."
    p.level = 1

    # Slide 6: Multi-Server Scaling (M/M/c)
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Horizontal Scaling & USL Bounds"

    content = slide.placeholders[1].text_frame
    content.text = "Extended solver to M/M/c multi-server queues using Erlang-C."
    p = content.add_paragraph()
    p.text = "Frontend saturation occurs at 12.5 req/s (Single replica)."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Scaling Frontend to 2 replicas drops utilization to 40% and Erlang-C queuing probability (P_Q) to 22.8%."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Universal Scalability Law (USL): Modeled contention and coherency penalties. Scaling past 9 pods degrades throughput due to Redis locking overhead."
    p.level = 1

    # Slide 7: Empirical Validation Results
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Empirical Validation & Results (at 10 req/s)"

    content = slide.placeholders[1].text_frame
    content.text = "Exceptional Predictive Accuracy on Critical Path:"
    p = content.add_paragraph()
    p.text = "Predicted E2E Response Time: 405.10 ms"
    p.level = 1
    p = content.add_paragraph()
    p.text = "Measured E2E Response Time: 423.52 ms (~4.3% Error)"
    p.level = 1
    p = content.add_paragraph()
    p.text = "Throughput-weighted MAPE: 11.5%"
    p.level = 1
    p = content.add_paragraph()
    p.text = "Theil's U Inequality Coefficient: 0.048"
    p.level = 1
    p = content.add_paragraph()
    p.text = "95% Confidence Interval Prediction Hit: The predicted 400.00 ms Frontend latency fell cleanly inside the [390.5 ms, 439.5 ms] empirical window."
    p.level = 1

    # Slide 8: Conclusion & Future Work
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Conclusions & Future Directions"

    content = slide.placeholders[1].text_frame
    content.text = "Analytical models remain indispensable for rapid capacity planning."
    p = content.add_paragraph()
    p.text = "Identified bottleneck (Frontend) with surgical precision."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Future Work: Layered Queueing Networks (LQN) to model synchronous thread blocking."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Future Work: Incorporate fixed TCP/Protobuf transit delay scalars."
    p.level = 1
    p = content.add_paragraph()
    p.text = "Future Work: Integrate M/M/c solver into Kubernetes KEDA operators for predictive autoscaling."
    p.level = 1

    prs.save("Microservice_Performance_Presentation.pptx")
    print("Presentation generated successfully!")


if __name__ == "__main__":
    create_presentation()
