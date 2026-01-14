from ultralytics import YOLO
import sys

def export_model():
    try:
        # Load the YOLOv8 model
        # Use 'pothole_best.pt' if you have valid weights, otherwise 'yolov8n.pt'
        model_name = "yolov8n.pt" 
        print(f"Loading {model_name}...")
        model = YOLO(model_name)

        # Export the model to TFLite format
        # format='tflite' exports to TFLite
        print("Exporting to TFLite...")
        model.export(format='tflite')
        
        print("Export complete!")
    except Exception as e:
        print(f"Error exporting model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    export_model()
