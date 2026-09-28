import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-16b444c9d053"

def seed_database():
    print(f"Connecting to Firestore with Project ID: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    
    tickets_ref = db.collection("tickets")
    
    initial_tickets = [
        {
            "ticket_id": "TCK-1001",
            "title": "VPN connection dropping frequently",
            "description": "User reports VPN drops every 15 minutes while working remotely.",
            "category": "Network",
            "priority": "High",
            "status": "In Progress",
            "requester": "alice@company.com",
            "assigned_to": "network-team@company.com",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        },
        {
            "ticket_id": "TCK-1002",
            "title": "Monitor flicker on USB-C dock",
            "description": "External display flickers when connected via Dell Thunderbolt dock.",
            "category": "Hardware",
            "priority": "Medium",
            "status": "Open",
            "requester": "bob@company.com",
            "assigned_to": "hardware-support@company.com",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        },
        {
            "ticket_id": "TCK-1003",
            "title": "Request access to Figma Pro workspace",
            "description": "New UI designer needs license access for the design system project.",
            "category": "Access",
            "priority": "Low",
            "status": "Resolved",
            "requester": "carol@company.com",
            "assigned_to": "it-admin@company.com",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    ]
    
    for ticket in initial_tickets:
        doc_ref = tickets_ref.document(ticket["ticket_id"])
        doc_ref.set(ticket)
        print(f"Seeded ticket {ticket['ticket_id']}: {ticket['title']}")
        
    print("Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
