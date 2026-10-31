"""
Wildlife Rarity & Threat Alert Service
Monitors camera-trap classifications for rare endangered species, dangerous apex predators,
and human-wildlife conflict threats. Triggers real-time alerts upon image upload.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

class WildlifeAlertService:
    """
    Evaluates ecological rarity status and danger threat levels for camera-trap wildlife detections.
    """

    # Comprehensive Registry of Rarity & Threat Taxa
    SPECIES_ALERT_REGISTRY: Dict[str, Dict[str, Any]] = {
        "mountain_lion": {
            "is_rare": True,
            "is_dangerous": True,
            "alert_level": "CRITICAL",
            "alert_type": "RARE_AND_DANGEROUS",
            "badge": "🚨 RARE APEX PREDATOR & DANGEROUS",
            "title": "🚨 CRITICAL ALERT: Rare & Dangerous Mountain Lion Detected!",
            "description": "Mountain Lion (Puma concolor) confirmed. Extremely rare solitary apex predator posing acute safety risk to field personnel and nearby livestock.",
            "conservation_status": "Vulnerable / Protected Apex Carnivore",
            "threat_level": "High Threat (Apex Carnivore - Human & Livestock Risk)",
            "safety_protocol": "1. Maintain minimum 150m standoff distance. 2. Broadcast immediate perimeter notification to field rangers. 3. Suspend lone field surveys in this grid."
        },
        "alaskan_tundra_wolf": {
            "is_rare": True,
            "is_dangerous": True,
            "alert_level": "CRITICAL",
            "alert_type": "RARE_AND_DANGEROUS",
            "badge": "🚨 RARE WOLF & DANGEROUS PREDATOR",
            "title": "🚨 CRITICAL ALERT: Rare Alaskan Tundra Wolf Sighting!",
            "description": "Alaskan Tundra Wolf (Canis lupus albus) identified. Highly endangered canid subspecies and apex pack hunter. High conservation priority.",
            "conservation_status": "Endangered Subspecies / High Conservation Priority",
            "threat_level": "High Threat (Apex Pack Hunter)",
            "safety_protocol": "1. Do not approach or corner. 2. Log exact coordinates for regional carnivore tracking. 3. Secure campsite food caches."
        },
        "wolf": {
            "is_rare": True,
            "is_dangerous": True,
            "alert_level": "CRITICAL",
            "alert_type": "RARE_AND_DANGEROUS",
            "badge": "🚨 RARE WOLF & DANGEROUS PREDATOR",
            "title": "🚨 CRITICAL ALERT: Rare Apex Wolf Detected!",
            "description": "Gray/Timber Wolf (Canis lupus) identified. Rare apex carnivore sighting with pack territorial implications.",
            "conservation_status": "Protected Apex Carnivore / Rare Sighting",
            "threat_level": "High Threat (Apex Pack Hunter)",
            "safety_protocol": "1. Alert field biologist patrol. 2. Verify radio collar frequencies if present. 3. Restrict nighttime trail access."
        },
        "bear": {
            "is_rare": True,
            "is_dangerous": True,
            "alert_level": "CRITICAL",
            "alert_type": "RARE_AND_DANGEROUS",
            "badge": "🚨 RARE & DANGEROUS LARGE CARNIVORE",
            "title": "🚨 CRITICAL ALERT: Dangerous Bear Detected!",
            "description": "Bear (Ursidae spp.) confirmed. Heavy apex omnivore capable of sudden defensive charges and property damage.",
            "conservation_status": "Protected Large Carnivore",
            "threat_level": "High Threat (Heavy Striking & Charge Hazard)",
            "safety_protocol": "1. Ready bear deterrents/spray. 2. Avoid sudden retreat; back away steadily. 3. Check for dependent cubs."
        },
        "tiger": {
            "is_rare": True,
            "is_dangerous": True,
            "alert_level": "CRITICAL",
            "alert_type": "RARE_AND_DANGEROUS",
            "badge": "🚨 CRITICALLY ENDANGERED & APEX DANGER",
            "title": "🚨 CRITICAL ALERT: Rare Endangered Tiger Detected!",
            "description": "Tiger (Panthera tigris) verified. Critically endangered apex feline requiring immediate anti-poaching and safety protection.",
            "conservation_status": "Critically Endangered / Global Red List",
            "threat_level": "Severe Danger (Ambush Apex Carnivore)",
            "safety_protocol": "1. Emergency security lockdown of sector. 2. Dispatch armed anti-poaching and conflict mitigation squad."
        },
        "lion": {
            "is_rare": True,
            "is_dangerous": True,
            "alert_level": "CRITICAL",
            "alert_type": "RARE_AND_DANGEROUS",
            "badge": "🚨 RARE APEX PREDATOR & DANGEROUS",
            "title": "🚨 CRITICAL ALERT: Rare Apex Lion Detected!",
            "description": "Lion (Panthera leo) verified. Apex social carnivore posing direct risk to unarmored personnel.",
            "conservation_status": "Vulnerable Apex Predator",
            "threat_level": "Severe Danger (Pride Apex Carnivore)",
            "safety_protocol": "1. Remain in enclosed vehicles. 2. Notify sector rangers and perimeter villages."
        },
        "elephant": {
            "is_rare": True,
            "is_dangerous": True,
            "alert_level": "CRITICAL",
            "alert_type": "RARE_AND_DANGEROUS",
            "badge": "🚨 RARE & POTENTIALLY DANGEROUS MEGAFAUNA",
            "title": "🚨 CRITICAL ALERT: Rare Elephant Megafauna Detected!",
            "description": "Elephant (Elephantidae spp.) detected. Endangered megaherbivore with potential for aggressive territorial charge and crop damage.",
            "conservation_status": "Endangered Megafauna",
            "threat_level": "High Threat (Charge & Trampling Risk)",
            "safety_protocol": "1. Maintain wide standoff (>100m). 2. Do not use camera flashes. 3. Monitor migratory herd movement."
        },
        "gray_fox": {
            "is_rare": True,
            "is_dangerous": False,
            "alert_level": "WARNING",
            "alert_type": "RARE_SPECIES",
            "badge": "🌟 RARE WILDLIFE SIGHTING",
            "title": "🌟 Rare Sighting: Elusive Gray Fox Detected!",
            "description": "Gray Fox (Urocyon cinereoargenteus) confirmed. Rare camera-trap detection; indigenous semi-arboreal canid of high conservation interest.",
            "conservation_status": "Protected Native Fauna / Elusive Sighting",
            "threat_level": "Harmless / Low Threat to Humans",
            "safety_protocol": "1. Record sighting in biodiversity catalog. 2. Harmless to humans; observe non-intrusively."
        },
        "coyote": {
            "is_rare": False,
            "is_dangerous": False,
            "alert_level": "INFO",
            "alert_type": "CAUTION_WILDLIFE",
            "badge": "⚠️ CAUTION: MESOPREDATOR",
            "title": "⚠️ Wildlife Advisory: Coyote Detected",
            "description": "Coyote (Canis latrans) detected. Common opportunistic mesopredator. Exercise standard caution around domestic pets.",
            "conservation_status": "Least Concern (Stable)",
            "threat_level": "Moderate Caution (Hazard to Small Pets / Poultry)",
            "safety_protocol": "1. Keep domestic animals secured. 2. Standard wilderness situational awareness."
        },
        "bobcat": {
            "is_rare": False,
            "is_dangerous": False,
            "alert_level": "INFO",
            "alert_type": "WILDLIFE_SIGHTING",
            "badge": "🐾 MESOCARNIVORE SIGHTING",
            "title": "🐾 Mesocarnivore Sighting: Bobcat",
            "description": "Bobcat (Lynx rufus) detected. Solitary native feline; naturally fearful of humans and strictly nocturnal/crepuscular.",
            "conservation_status": "Least Concern",
            "threat_level": "Low Threat (Avoids Human Contact)",
            "safety_protocol": "1. No action required; normal ecological presence."
        }
    }

    # Keyword patterns for dynamically recognizing global rare/dangerous taxa (from ImageNet classes)
    DANGEROUS_KEYWORDS = [
        "lion", "tiger", "leopard", "jaguar", "panther", "cougar", "puma",
        "wolf", "bear", "grizzly", "polar bear", "elephant", "rhino", "hippo",
        "alligator", "crocodile", "hyena", "cheetah", "snow leopard", "cobra",
        "viper", "mamba", "rattlesnake", "wolverine"
    ]

    RARE_KEYWORDS = [
        "lion", "tiger", "leopard", "jaguar", "snow leopard", "cheetah",
        "tundra wolf", "wolf", "bear", "elephant", "rhino", "gorilla", "panda",
        "chimpanzee", "orangutan", "tapir", "wolverine", "gray fox"
    ]

    @classmethod
    def evaluate_animal_alert(
        cls,
        species_key: str,
        common_name: str = "",
        confidence: float = 1.0,
        location: str = "loc_01",
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates species classification and returns structured rarity & threat alert telemetry.
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sp_key = (species_key or "").lower().strip()
        common_lower = (common_name or "").lower().strip()

        # 1. Check exact key in registry
        if sp_key in cls.SPECIES_ALERT_REGISTRY:
            reg = cls.SPECIES_ALERT_REGISTRY[sp_key]
            is_rare = reg["is_rare"]
            is_dangerous = reg["is_dangerous"]
            has_alert = is_rare or is_dangerous

            return {
                "has_alert": has_alert,
                "is_rare": is_rare,
                "is_dangerous": is_dangerous,
                "alert_level": reg["alert_level"],
                "alert_type": reg["alert_type"],
                "badge": reg["badge"],
                "title": reg["title"],
                "message": f"{reg['description']} Detected at {location}.",
                "conservation_status": reg["conservation_status"],
                "threat_level": reg["threat_level"],
                "safety_protocol": reg["safety_protocol"],
                "species": species_key,
                "common_name": common_name or reg["title"].split(":")[1].strip() if ":" in reg["title"] else species_key,
                "confidence": round(confidence, 4),
                "location": location,
                "timestamp": timestamp
            }

        # 2. Check dynamic keywords for ImageNet taxa
        combined_text = f"{sp_key} {common_lower}"
        is_dangerous = any(kw in combined_text for kw in cls.DANGEROUS_KEYWORDS)
        is_rare = any(kw in combined_text for kw in cls.RARE_KEYWORDS)

        if is_rare and is_dangerous:
            return {
                "has_alert": True,
                "is_rare": True,
                "is_dangerous": True,
                "alert_level": "CRITICAL",
                "alert_type": "RARE_AND_DANGEROUS",
                "badge": "🚨 RARE & DANGEROUS ANIMAL",
                "title": f"🚨 CRITICAL ALERT: Rare & Dangerous {common_name or species_key.title()} Detected!",
                "message": f"Confirmed detection of {common_name or species_key.title()} at {location}. High conservation priority and active danger threat.",
                "conservation_status": "Protected / Rare Wildlife Sighting",
                "threat_level": "High Threat (Dangerous Wildlife / Predator)",
                "safety_protocol": "1. Maintain safe distance. 2. Issue field notification to park personnel. 3. Monitor camera station logs.",
                "species": species_key,
                "common_name": common_name or species_key.replace('_', ' ').title(),
                "confidence": round(confidence, 4),
                "location": location,
                "timestamp": timestamp
            }
        elif is_dangerous:
            return {
                "has_alert": True,
                "is_rare": False,
                "is_dangerous": True,
                "alert_level": "WARNING",
                "alert_type": "DANGEROUS_WILDLIFE",
                "badge": "⚠️ DANGEROUS WILDLIFE ALERT",
                "title": f"⚠️ DANGER ALERT: Dangerous {common_name or species_key.title()} Detected!",
                "message": f"Potentially dangerous wildlife ({common_name or species_key.title()}) sighted at {location}. Field caution advised.",
                "conservation_status": "Monitored Wildlife",
                "threat_level": "High Threat to Humans / Domestic Stock",
                "safety_protocol": "1. Advise field parties in sector. 2. Verify secure perimeter barriers.",
                "species": species_key,
                "common_name": common_name or species_key.replace('_', ' ').title(),
                "confidence": round(confidence, 4),
                "location": location,
                "timestamp": timestamp
            }
        elif is_rare:
            return {
                "has_alert": True,
                "is_rare": True,
                "is_dangerous": False,
                "alert_level": "WARNING",
                "alert_type": "RARE_SPECIES",
                "badge": "🌟 RARE SPECIES SIGHTING",
                "title": f"🌟 Rare Wildlife Alert: {common_name or species_key.title()} Detected!",
                "message": f"Rare species sighting ({common_name or species_key.title()}) recorded at {location}. Valuable biological telemetry.",
                "conservation_status": "Vulnerable / Rare Occurrence",
                "threat_level": "Harmless / Low Threat",
                "safety_protocol": "1. Log high-resolution frame for ecological registry. 2. Harmless to humans.",
                "species": species_key,
                "common_name": common_name or species_key.replace('_', ' ').title(),
                "confidence": round(confidence, 4),
                "location": location,
                "timestamp": timestamp
            }

        # 3. Standard Non-Alert Wildlife (deer, rabbit, bird, empty, etc.)
        return {
            "has_alert": False,
            "is_rare": False,
            "is_dangerous": False,
            "alert_level": "NORMAL",
            "alert_type": "NONE",
            "badge": "NORMAL WILDLIFE",
            "title": f"{common_name or species_key.title()}",
            "message": f"Normal wildlife activity recorded at {location}.",
            "conservation_status": "Stable / Least Concern",
            "threat_level": "Harmless",
            "safety_protocol": "Standard camera-trap observation.",
            "species": species_key,
            "common_name": common_name or species_key.replace('_', ' ').title(),
            "confidence": round(confidence, 4),
            "location": location,
            "timestamp": timestamp
        }

    @classmethod
    def summarize_batch_alerts(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates batch upload items and compiles high-level alert warnings.
        """
        alerts = []
        rare_items = []
        dangerous_items = []
        critical_items = []

        for item in items:
            alert = item.get("alert")
            if not alert and not item.get("is_empty"):
                # Evaluate on the fly if missing
                alert = cls.evaluate_animal_alert(
                    species_key=item.get("species", "empty"),
                    common_name=item.get("common_name", ""),
                    confidence=float(item.get("confidence", 0.0)),
                    location=item.get("location", "loc_01"),
                    timestamp=item.get("datetime") or item.get("timestamp")
                )
                item["alert"] = alert
                item["is_rare"] = alert["is_rare"]
                item["is_dangerous"] = alert["is_dangerous"]

            if alert and alert.get("has_alert"):
                alerts.append(alert)
                if alert.get("is_rare"):
                    rare_items.append(alert)
                if alert.get("is_dangerous"):
                    dangerous_items.append(alert)
                if alert.get("alert_level") == "CRITICAL":
                    critical_items.append(alert)

        has_alerts = len(alerts) > 0
        unique_alert_species = sorted(list({a.get("common_name") or a.get("species") for a in alerts}))

        headline = ""
        advisory = ""
        if critical_items:
            headline = f"🚨 CRITICAL WILDLIFE ALERT: {len(critical_items)} Rare & Dangerous Animal Detection(s)!"
            advisory = (
                f"Urgent: Dangerous apex predator / rare megafauna detected in batch ({', '.join(unique_alert_species)}). "
                "Field personnel in this station sector must be warned immediately. Maintain safety standoff distance."
            )
        elif dangerous_items:
            headline = f"⚠️ DANGEROUS WILDLIFE ALERT: {len(dangerous_items)} Warning Detection(s)!"
            advisory = f"Caution advised: Potentially dangerous wildlife ({', '.join(unique_alert_species)}) detected in this batch."
        elif rare_items:
            headline = f"🌟 RARE SPECIES SIGHTING: {len(rare_items)} Rare Wildlife Detection(s)!"
            advisory = f"High ecological interest: Rare animal species ({', '.join(unique_alert_species)}) recorded in this batch."

        return {
            "has_alerts": has_alerts,
            "total_alerts": len(alerts),
            "rare_alerts_count": len(rare_items),
            "dangerous_alerts_count": len(dangerous_items),
            "critical_alerts_count": len(critical_items),
            "alert_species": unique_alert_species,
            "headline": headline,
            "advisory": advisory,
            "alerts": alerts
        }

alert_service = WildlifeAlertService()
