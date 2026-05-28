# --- NARAYAN: OFFLINE DISASTER DNS SERVER ---
# --- ADVANCED DNS SERVER FOR ANDROID/IOS ---
import socket
from dnslib import DNSRecord, QTYPE, RR, A
from dnslib import DNSHeader as DNSServerHeader

DNS_PORT = 53

# Ye wo domains hain jo Android/iPhone check karte hain internet test karne ke liye
CAPTIVE_DOMAINS = [
    "connectivitycheck.gstatic.com",
    "clients3.google.com",
    "www.google.com",
    "connectivitycheck.android.com",
    "msftconnecttest.com",  # Windows
    "www.msftconnecttest.com",
    "captive.apple.com"     # iPhone
]

def start_dns_service(server_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock.bind(('0.0.0.0', DNS_PORT))
        print(f"\n[DNS] ANDROID TRAP ACTIVATED on {server_ip}")
        
        while True:
            data, addr = sock.recvfrom(512)
            try:
                request = DNSRecord.parse(data)
                qname = str(request.q.qname).rstrip('.') # Last dot hata do
                
                # Logic: Agar koi device Internet check kar raha hai, to use pakad lo
                # Ya agar wo 'google.com' maang raha hai tab bhi
                
                reply = DNSRecord(DNSServerHeader(id=request.header.id, qr=1, aa=1, ra=1), q=request.q)
                
                # Har request ke badle apna IP dena (Aggressive Mode)
                reply.add_answer(RR(request.q.qname, QTYPE.A, rdata=A(server_ip), ttl=0))
                
                sock.sendto(reply.pack(), addr)
                
            except Exception:
                pass 
    except Exception as e:
        print(f"[DNS ERROR] {e}")
    finally:
        sock.close()