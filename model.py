from ultralytics import YOLO

class PipelineModel:
    def __init__(self, car_model_path, plate_model_path, char_model_path):
        self.car_model = YOLO(r'D:\oman_car_plates\MODELS\vehicle_detection.pt')
 
        self.plate_model = YOLO(r'D:\oman_car_plates\MODELS\licensePlate.pt')  
        self.char_model = YOLO(r'D:\oman_car_plates\MODELS\best(2).pt') 

    def detect(self, frame):
        # Step 1: Detect cars
        car_results = self.car_model.predict(frame)
        car_boxes = car_results[0].boxes

        plates = []
        for car_box in car_boxes:
            x1, y1, x2, y2 = map(int, car_box.xyxy[0])
            car_crop = frame[y1:y2, x1:x2]

            # Step 2: Detect plates within each car
            plate_results = self.plate_model.predict(car_crop)
            plate_boxes = plate_results[0].boxes

            for plate_box in plate_boxes:
                px1, py1, px2, py2 = map(int, plate_box.xyxy[0])
                plate_crop = car_crop[py1:py2, px1:px2]
                plates.append((x1 + px1, y1 + py1, x1 + px2, y1 + py2, plate_crop))

        characters = []
        for plate in plates:
            px1, py1, px2, py2, plate_crop = plate

            # Step 3: Detect characters within each plate
            char_results = self.char_model.predict(plate_crop)
            char_boxes = char_results[0].boxes

            for char_box in char_boxes:
                cx1, cy1, cx2, cy2 = map(int, char_box.xyxy[0])
                characters.append((px1 + cx1, py1 + cy1, px1 + cx2, py1 + cy2))

        return car_boxes, plates, characters