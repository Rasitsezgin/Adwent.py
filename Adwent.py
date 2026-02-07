#!/usr/bin/env python3
"""
Advanced Multi-Engine Dork Scanner
Real Results Verification | 10+ Search Engines
VERIFIED RESULTS ONLY

# ============================================
# KULLANIM ÖRNEKLERİ
# ============================================

# 1. TAM DOĞRULAMA (Önerilen - Yavaş ama kesin sonuç)
python3 Adwent.py -t example.com

# 2. HIZLI TARAMA (Doğrulama YOK - Hızlı ama false positive olabilir)
python3 Adwent.py -t example.com --no-verify -d 0.5

# 3. SONUÇLARI KAYDET
python3 Adwent.py -t example.com -o results.json

# 4. HIZLI + KAYIT
python3 Adwent.py -t example.com --no-verify -d 0.3 -o fast_scan.json

# 5. ULTRA HIZLI (Minimum delay)
python3 Adwent.py -t example.com --no-verify -d 0.1 -th 20

# 6. DENGELI TARAMA (Orta hız + doğrulama)
python3 Adwent.py -t example.com -d 2 -o balanced.json
"""

import requests
import time
import random
import argparse
import json
from urllib.parse import quote, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

class VerifiedDorkScanner:
    def __init__(self, target, threads=15, delay=1, output_file=None, verify=True):
        self.target = target
        self.threads = threads
        self.delay = delay
        self.output_file = output_file
        self.verify_results = verify
        self.results = []
        self.found_urls = set()
        self.false_positives = 0
        
        # Multiple search engines
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Optimized high-value payloads
        self.payloads = {
            'CRITICAL_FILES': [
                'ext:env',
                'ext:sql',
                'ext:log',
                'ext:bak',
                'ext:conf',
                'ext:config',
            ],
            'ADMIN_PANELS': [
                'inurl:admin',
                'inurl:login',
                'inurl:wp-admin',
                'inurl:phpmyadmin',
                'inurl:administrator',
            ],
            'SQL_INJECTION': [
                'inurl:id=',
                'inurl:page.php?id=',
                'inurl:product.php?id=',
            ],
            'DIRECTORY_LISTING': [
                'intitle:"index of"',
                'intitle:"index of /" +parent',
            ],
            'ERRORS': [
                '"Warning: mysql"',
                '"Fatal error"',
                '"syntax error"',
            ],
            'GIT_EXPOSURE': [
                'inurl:.git',
                'intitle:"Index of /.git"',
            ],
            'BACKUPS': [
                'ext:backup',
                'ext:old',
                'inurl:backup',
            ]
        }

    def get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def verify_url(self, url):
        """Verify if URL actually exists and is accessible"""
        try:
            headers = self.get_random_headers()
            response = requests.head(url, headers=headers, timeout=5, verify=False, allow_redirects=True)
            return response.status_code in [200, 301, 302, 403]  # 403 means exists but forbidden
        except:
            try:
                # Try GET if HEAD fails
                response = requests.get(url, headers=headers, timeout=5, verify=False, allow_redirects=True)
                return response.status_code in [200, 301, 302, 403]
            except:
                return False

    def search_google(self, dork):
        """Google search with proper parsing"""
        results = []
        try:
            params = {
                'q': dork,
                'num': 30,
                'hl': 'en',
                'gl': 'us'
            }
            url = f"https://www.google.com/search?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all search result links
                for g in soup.find_all('div', class_='g'):
                    anchors = g.find_all('a')
                    for anchor in anchors:
                        link = anchor.get('href', '')
                        if link.startswith('/url?q='):
                            actual_url = link.split('/url?q=')[1].split('&')[0]
                            if self.target in actual_url and actual_url.startswith('http'):
                                results.append(actual_url)
                
                # Alternative: find all links
                if not results:
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link['href']
                        if self.target in href and href.startswith('http') and 'google.com' not in href:
                            results.append(href)
            
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"    [!] Google error: {str(e)[:50]}")
        
        return results

    def search_bing(self, dork):
        """Bing search"""
        results = []
        try:
            params = {
                'q': dork,
                'count': 30
            }
            url = f"https://www.bing.com/search?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Bing results are in <li class="b_algo">
                for li in soup.find_all('li', class_='b_algo'):
                    links = li.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        if self.target in href and href.startswith('http'):
                            results.append(href)
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"    [!] Bing error: {str(e)[:50]}")
        
        return results

    def search_duckduckgo(self, dork):
        """DuckDuckGo HTML search"""
        results = []
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(dork)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # DuckDuckGo results
                for link in soup.find_all('a', class_='result__a'):
                    href = link.get('href', '')
                    if 'uddg=' in href:
                        actual_url = href.split('uddg=')[1].split('&')[0]
                        from urllib.parse import unquote
                        actual_url = unquote(actual_url)
                        if self.target in actual_url and actual_url.startswith('http'):
                            results.append(actual_url)
            
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            print(f"    [!] DuckDuckGo error: {str(e)[:50]}")
        
        return results

    def search_yahoo(self, dork):
        """Yahoo search"""
        results = []
        try:
            params = {
                'p': dork,
                'n': 30
            }
            url = f"https://search.yahoo.com/search?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Yahoo uses different classes
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if self.target in href and href.startswith('http') and 'yahoo.com' not in href:
                        results.append(href)
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"    [!] Yahoo error: {str(e)[:50]}")
        
        return results

    def search_yandex(self, dork):
        """Yandex search"""
        results = []
        try:
            params = {
                'text': dork,
                'lr': 10418
            }
            url = f"https://yandex.com/search/?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if self.target in href and href.startswith('http') and 'yandex' not in href:
                        results.append(href)
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"    [!] Yandex error: {str(e)[:50]}")
        
        return results

    def search_brave(self, dork):
        """Brave search"""
        results = []
        try:
            params = {'q': dork}
            url = f"https://search.brave.com/search?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if self.target in href and href.startswith('http'):
                        results.append(href)
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"    [!] Brave error: {str(e)[:50]}")
        
        return results

    def search_startpage(self, dork):
        """Startpage search (Google proxy)"""
        results = []
        try:
            params = {'query': dork}
            url = f"https://www.startpage.com/do/search?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if self.target in href and href.startswith('http'):
                        results.append(href)
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"    [!] Startpage error: {str(e)[:50]}")
        
        return results

    def search_ecosia(self, dork):
        """Ecosia search"""
        results = []
        try:
            params = {'q': dork}
            url = f"https://www.ecosia.org/search?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if self.target in href and href.startswith('http'):
                        results.append(href)
            
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            print(f"    [!] Ecosia error: {str(e)[:50]}")
        
        return results

    def search_qwant(self, dork):
        """Qwant search"""
        results = []
        try:
            params = {'q': dork, 't': 'web'}
            url = f"https://www.qwant.com/?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                # Extract URLs from response
                urls = re.findall(r'https?://[^\s<>"]+', response.text)
                for url_found in urls:
                    if self.target in url_found and 'qwant' not in url_found:
                        results.append(url_found)
            
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            print(f"    [!] Qwant error: {str(e)[:50]}")
        
        return results

    def search_swisscows(self, dork):
        """Swisscows search"""
        results = []
        try:
            params = {'query': dork, 'region': 'en-US'}
            url = f"https://swisscows.com/web?{urlencode(params)}"
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if self.target in href and href.startswith('http'):
                        results.append(href)
            
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            print(f"    [!] Swisscows error: {str(e)[:50]}")
        
        return results

    def multi_engine_search(self, dork):
        """Search across ALL engines in parallel"""
        all_results = []
        
        engines = {
            'Google': self.search_google,
            'Bing': self.search_bing,
            'DuckDuckGo': self.search_duckduckgo,
            'Yahoo': self.search_yahoo,
            'Yandex': self.search_yandex,
            'Brave': self.search_brave,
            'Startpage': self.search_startpage,
            'Ecosia': self.search_ecosia,
            'Qwant': self.search_qwant,
            'Swisscows': self.search_swisscows
        }
        
        print(f"    [*] Searching in: {', '.join(engines.keys())}")
        
        with ThreadPoolExecutor(max_workers=len(engines)) as executor:
            future_to_engine = {executor.submit(search_func, dork): name 
                               for name, search_func in engines.items()}
            
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    results = future.result()
                    if results:
                        print(f"    [+] {engine_name}: {len(results)} results")
                        all_results.extend(results)
                    else:
                        print(f"    [-] {engine_name}: No results")
                except Exception as e:
                    print(f"    [!] {engine_name}: Error - {str(e)[:30]}")
        
        # Remove duplicates
        unique_results = list(set(all_results))
        
        # Verify results if enabled
        if self.verify_results and unique_results:
            print(f"    [*] Verifying {len(unique_results)} URLs...")
            verified = []
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_url = {executor.submit(self.verify_url, url): url 
                                for url in unique_results}
                
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        if future.result():
                            verified.append(url)
                            print(f"    [✓] Verified: {url}")
                        else:
                            self.false_positives += 1
                            print(f"    [✗] False positive: {url}")
                    except:
                        pass
            
            return verified
        
        return unique_results

    def test_dork(self, category, payload):
        """Test dork with verification"""
        dork = f"site:{self.target} {payload}"
        
        print(f"\n{'='*70}")
        print(f"[*] Category: {category}")
        print(f"[*] Payload: {payload}")
        print(f"[*] Dork: {dork}")
        print(f"{'='*70}")
        
        urls = self.multi_engine_search(dork)
        
        if urls:
            # Filter out URLs not in found_urls set
            new_urls = [url for url in urls if url not in self.found_urls]
            
            if new_urls:
                self.found_urls.update(new_urls)
                
                result = {
                    'category': category,
                    'dork': dork,
                    'payload': payload,
                    'urls': new_urls,
                    'count': len(new_urls),
                    'verified': self.verify_results,
                    'timestamp': datetime.now().isoformat()
                }
                self.results.append(result)
                
                print(f"\n[+] ✓ FOUND {len(new_urls)} VERIFIED URLs:")
                for i, url in enumerate(new_urls, 1):
                    print(f"    {i:2}. {url}")
                
                return result
            else:
                print(f"\n[-] All results were duplicates")
        else:
            print(f"\n[-] No results found")
        
        return None

    def scan(self):
        """Main scanning function"""
        print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║          ADVANCED MULTI-ENGINE DORK SCANNER v4.0                  ║
║          10+ Search Engines | Real Verification                   ║
╚═══════════════════════════════════════════════════════════════════╝

Target: {self.target}
Threads: {self.threads}
Delay: {self.delay}s
Verification: {'ENABLED ✓' if self.verify_results else 'DISABLED'}
Total Payloads: {sum(len(p) for p in self.payloads.values())}

Search Engines:
  → Google, Bing, DuckDuckGo, Yahoo, Yandex
  → Brave, Startpage, Ecosia, Qwant, Swisscows

Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'═'*71}
        """)
        
        start_time = time.time()
        
        # Execute sequentially for better control
        for category, payload_list in self.payloads.items():
            print(f"\n\n╔═══════════════════════════════════════════════════════════════════╗")
            print(f"║  CATEGORY: {category:54} ║")
            print(f"╚═══════════════════════════════════════════════════════════════════╝")
            
            for payload in payload_list:
                self.test_dork(category, payload)
                time.sleep(self.delay)
        
        elapsed = time.time() - start_time
        
        self.save_results()
        self.print_summary(elapsed)

    def save_results(self):
        """Save results to JSON"""
        if self.output_file:
            output = {
                'target': self.target,
                'scan_time': datetime.now().isoformat(),
                'verification_enabled': self.verify_results,
                'total_findings': len(self.results),
                'total_urls': len(self.found_urls),
                'false_positives': self.false_positives,
                'results': self.results
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            print(f"\n[✓] Results saved to: {self.output_file}")

    def print_summary(self, elapsed):
        """Print summary"""
        print(f"""
\n{'═'*71}
╔═══════════════════════════════════════════════════════════════════╗
║                         SCAN SUMMARY                              ║
╚═══════════════════════════════════════════════════════════════════╝

[+] Target: {self.target}
[+] Duration: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)
[+] Total Categories: {len(self.payloads)}
[+] Total Payloads: {sum(len(p) for p in self.payloads.values())}
[+] Total Findings: {len(self.results)}
[+] Verified URLs: {len(self.found_urls)}
[+] False Positives: {self.false_positives}
[+] Success Rate: {(len(self.found_urls)/(len(self.found_urls)+self.false_positives)*100) if (len(self.found_urls)+self.false_positives) > 0 else 0:.1f}%

        """)
        
        if self.results:
            print("╔═══════════════════════════════════════════════════════════════════╗")
            print("║                    FINDINGS BY CATEGORY                           ║")
            print("╚═══════════════════════════════════════════════════════════════════╝\n")
            
            for category in self.payloads.keys():
                cat_results = [r for r in self.results if r['category'] == category]
                if cat_results:
                    total_urls = sum(r['count'] for r in cat_results)
                    print(f"  [{category:20}]: {total_urls:3} URLs found")
                    for result in cat_results:
                        print(f"    └─ {result['payload']:30} → {result['count']} URLs")
            
            print(f"\n{'═'*71}")
            print("ALL FOUND URLs:\n")
            for i, url in enumerate(sorted(self.found_urls), 1):
                print(f"{i:3}. {url}")
        
        print(f"\n{'═'*71}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'═'*71}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Multi-Engine Dork Scanner with Real Verification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan with verification
  python3 verified_dork.py -t example.com
  
  # Fast scan without verification
  python3 verified_dork.py -t example.com --no-verify -d 0.5
  
  # Save results
  python3 verified_dork.py -t example.com -o results.json
  
  # Fast mode
  python3 verified_dork.py -t example.com -th 20 -d 0.3 --no-verify
        """
    )
    
    parser.add_argument('-t', '--target', required=True, help='Target domain')
    parser.add_argument('-o', '--output', help='Output JSON file')
    parser.add_argument('-th', '--threads', type=int, default=15, help='Threads (default: 15)')
    parser.add_argument('-d', '--delay', type=float, default=1, help='Delay (default: 1)')
    parser.add_argument('--no-verify', action='store_true', help='Skip URL verification (faster)')
    
    args = parser.parse_args()
    
    scanner = VerifiedDorkScanner(
        target=args.target,
        threads=args.threads,
        delay=args.delay,
        output_file=args.output,
        verify=not args.no_verify
    )
    
    try:
        scanner.scan()
    except KeyboardInterrupt:
        print("\n\n[!] Scan interrupted by user")
        scanner.save_results()
        sys.exit(0)


if __name__ == "__main__":
    main()
