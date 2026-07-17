import torch
import timm
import cv2
import numpy as np

from torchvision import transforms


class ViolenceDetector:

    def __init__(self, model_path):

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model = timm.create_model(
            "efficientnet_b0",
            pretrained=False,
            num_classes=2
        )

        self.model.load_state_dict(
            torch.load(
                model_path,
                map_location=self.device
            )
        )

        self.model.to(self.device)

        self.model.eval()

        self.transform = transforms.Compose([

            transforms.ToPILImage(),

            transforms.Resize((224, 224)),

            transforms.ToTensor(),

            transforms.Normalize(

                mean=[0.485, 0.456, 0.406],

                std=[0.229, 0.224, 0.225]

            )

        ])

    # ---------------------------------------------------------

    def predict(self, frame):

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        image = self.transform(rgb)

        image = image.unsqueeze(0).to(self.device)

        with torch.no_grad():

            outputs = self.model(image)

            probabilities = torch.softmax(outputs, dim=1)

            confidence, prediction = torch.max(
                probabilities,
                1
            )

        if prediction.item() == 0:

            label = "NonViolence"

        else:

            label = "Violence"

        return {

            "label": label,

            "confidence": float(confidence.item()),

            "violence_probability": float(
                probabilities[0][1].item()
            )

        }