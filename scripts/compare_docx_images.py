import sys
sys.stdout.reconfigure(encoding='utf-8')
import zipfile, hashlib, os

target_figures = {
    "media/image2.png": "results/figures/figure1_reconstructed_call_graph.png",
    "media/image3.png": "results/figures/figure2_lqn_three_tier_architecture.png",
    "media/image4.png": "results/figures/figure3_utilisation_spectrum.png",
    "media/image10.png": "results/figures/utilization_vs_arrival_rate.png",
    "media/image5.png": "results/figures/figure4_predictions_vs_measurements.png",
    "media/image6.png": "results/figures/figure5_hockey_stick_knee_curve.png",
    "media/image9.png": "results/figures/system_response_time.png",
    "media/image7.png": "results/figures/figure6_multi_replica_scaling.png",
    "media/image8.png": "results/figures/figure7_sensitivity_tornado.png",
}

with zipfile.ZipFile('SPEFinal.docx', 'r') as z:
    for docx_img, disk_img in target_figures.items():
        docx_bytes = z.read('word/' + docx_img)
        docx_hash = hashlib.sha256(docx_bytes).hexdigest()
        
        if os.path.exists(disk_img):
            with open(disk_img, 'rb') as f:
                disk_bytes = f.read()
            disk_hash = hashlib.sha256(disk_bytes).hexdigest()
            match = "MATCH (Identical)" if docx_hash == disk_hash else "DIFFERS (Needs update)"
        else:
            match = "Disk file missing"
            disk_hash = "N/A"
            
        print(f"{docx_img} vs {os.path.basename(disk_img)}: {match}")
