import cv2
import numpy as np
import torch
import torch.nn.functional as F
import timm

from utils.config import (
    VIOLENCE_MODEL,
    VIOLENCE_THRESHOLD,
    VIOLENCE_WINDOW,
    VIOLENCE_WINDOW_VOTES,
)


class ViolenceDetector:
    """
    Violence detector backed by the trained EfficientNet-B0 classifier
    (violence_classifier.pth, test F1 0.953 on the Real Life Violence
    Situations dataset).

    A sliding window of frames is classified individually; the window is
    "violent" when at least VIOLENCE_WINDOW_VOTES of the last
    VIOLENCE_WINDOW frames are classified violent above the threshold.
    This temporal voting suppresses single-frame false positives.

    Returns:
    {
        "violence": bool,
        "score": float,          # smoothed confidence 0..1 for the window
        "frame_confidence": float,  # confidence of the current frame
        "window_votes": int,
        "frame": annotated_frame
    }
    """

    def __init__(
        self,
        model_path=VIOLENCE_MODEL,
        threshold=VIOLENCE_THRESHOLD,
        window=VIOLENCE_WINDOW,
        votes=VIOLENCE_WINDOW_VOTES,
    ):
        self.threshold = threshold

        self.window_size = window

        self.votes_required = votes

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = timm.create_model(
            "efficientnet_b0",
            pretrained=False,
            num_classes=2,
        )

        state = torch.load(
            str(model_path),
            map_location=self.device,
            weights_only=True,
        )

        state = {
            k[7:] if k.startswith("module.") else k: v
            for k, v in state.items()
        }

        self.model.load_state_dict(state)

        self.model.to(self.device)

        self.model.eval()

        # ImageNet normalization, matching training transforms
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)

        self.std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

        self.window = []  # rolling list of per-frame (is_violent, confidence)

    def _classify(self, frame):
        """
        Run the classifier on a single frame. Returns (is_violent, confidence).
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        rgb = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_LINEAR)

        tensor = torch.from_numpy(rgb).float().permute(2, 0, 1) / 255.0

        tensor = (tensor - self.mean) / self.std

        tensor = tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)

            probs = F.softmax(logits, dim=1)[0]

        confidence = float(probs[1])  # class 1 = Violence

        return confidence >= self.threshold, confidence

    def detect(self, frame):
        annotated = frame.copy()

        is_violent, confidence = self._classify(frame)

        self.window.append((is_violent, confidence))

        if len(self.window) > self.window_size:
            self.window.pop(0)

        votes = sum(1 for v, _ in self.window if v)

        violence = len(self.window) >= self.window_size and votes >= self.votes_required

        # Mean confidence of the window, for display/alerts
        score = sum(c for _, c in self.window) / len(self.window) if self.window else 0.0

        if violence:
            cv2.putText(
                annotated,
                f"VIOLENCE DETECTED ({votes}/{self.window_size})",
                (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3,
            )

        return {
            "violence": violence,
            "score": round(score, 3),
            "frame_confidence": round(confidence, 3),
            "window_votes": votes,
            "frame": annotated,
        }

    def reset(self):
        self.window = []


violence_detector = ViolenceDetector()
