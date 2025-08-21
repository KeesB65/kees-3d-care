import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import laspy
from scipy.spatial import cKDTree
import os
import sys
import traceback
from tqdm import tqdm

def show_error(title, message):
    """Show error dialog and print to console"""
    print(f"❌ {title}: {message}")
    try:
        messagebox.showerror(title, message)
    except:
        pass  # In case GUI is not available
    
def show_info(title, message):
    """Show info dialog and print to console"""
    print(f"ℹ️  {title}: {message}")
    try:
        messagebox.showinfo(title, message)
    except:
        pass

def validate_las_file(file_path, file_description):
    """Validate that a LAS file exists and can be read"""
    if not file_path:
        raise ValueError(f"Geen {file_description} geselecteerd")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_description} bestand niet gevonden: {file_path}")
    
    if not file_path.lower().endswith('.las'):
        raise ValueError(f"{file_description} moet een .las bestand zijn")
    
    # Try to read the file header to validate it's a proper LAS file
    try:
        with laspy.open(file_path) as f:
            header = f.header
            if header.point_count == 0:
                raise ValueError(f"{file_description} bevat geen punten")
    except Exception as e:
        raise ValueError(f"{file_description} is niet een geldig LAS bestand: {str(e)}")

def main():
    """Main function with comprehensive error handling"""
    try:
        # === GUI Setup
        try:
            root = tk.Tk()
            root.withdraw()
            
            print("📂 Kies DOEL puntenwolk zonder kleur (.las)")
            target_path = filedialog.askopenfilename(title="Puntenwolk zonder kleur", filetypes=[("LAS bestanden", "*.las")])
            
            # Validate target file selection
            try:
                validate_las_file(target_path, "Doel puntenwolk")
            except (ValueError, FileNotFoundError) as e:
                show_error("Probleem met doelbestand", str(e))
                sys.exit(1)
            
            print("📂 Kies GEKLEURDE puntenwolk (.las)")
            source_path = filedialog.askopenfilename(title="Gekleurde LAS-bestand", filetypes=[("LAS bestanden", "*.las")])
            
            # Validate source file selection
            try:
                validate_las_file(source_path, "Bron puntenwolk")
            except (ValueError, FileNotFoundError) as e:
                show_error("Probleem met bronbestand", str(e))
                sys.exit(1)
            
            print("💾 Kies waar je de output wilt opslaan")
            output_path = filedialog.asksaveasfilename(title="Opslaan als", defaultextension=".las", filetypes=[("LAS bestanden", "*.las")])
            if not output_path:
                print("❌ Geen uitvoerbestand geselecteerd. Afgebroken.")
                sys.exit(0)
            
            # Validate output directory exists and is writable
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                show_error("Output folder probleem", f"De output folder bestaat niet: {output_dir}")
                sys.exit(1)
            
            if not os.access(output_dir, os.W_OK):
                show_error("Toegang geweigerd", f"Geen schrijftoegang tot output folder: {output_dir}")
                sys.exit(1)

        except Exception as e:
            show_error("GUI Initialisatie Fout", f"Probleem bij starten van de gebruikersinterface: {str(e)}\n\nMogelijke oplossingen:\n- Zorg dat je een grafische desktop hebt\n- Installeer tkinter: pip install tk")
            sys.exit(1)

        # === Laad target om aantal punten te weten
        try:
            print("📥 Lees doelbestand (zonder kleur)...")
            target_las = laspy.read(target_path)
            tgt_xyz_full = np.vstack((target_las.x, target_las.y, target_las.z)).T
            num_total = len(tgt_xyz_full)
            
            if num_total == 0:
                show_error("Leeg bestand", "Het doelbestand bevat geen punten.")
                sys.exit(1)
                
            print(f"✅ Doelbestand geladen: {num_total:,} punten")
            
            # Check memory requirements
            memory_estimate_mb = (num_total * 32) / (1024 * 1024)  # Rough estimate
            if memory_estimate_mb > 2000:  # More than 2GB
                print(f"⚠️  Waarschuwing: Groot bestand gedetecteerd ({memory_estimate_mb:.0f} MB verwacht geheugengebruik)")
                print("   Overweeg om een lager percentage te gebruiken in de volgende stap.")
                
        except FileNotFoundError:
            show_error("Bestand niet gevonden", f"Het doelbestand kan niet worden gevonden: {target_path}")
            sys.exit(1)
        except MemoryError:
            show_error("Onvoldoende geheugen", f"Het doelbestand is te groot om in het geheugen te laden ({num_total:,} punten).\n\nProbeer:\n- Een kleiner bestand te gebruiken\n- Meer RAM geheugen beschikbaar te maken")
            sys.exit(1)
        except Exception as e:
            show_error("Fout bij laden doelbestand", f"Onverwachte fout bij het lezen van het doelbestand:\n{str(e)}\n\nControleer of het bestand niet beschadigd is.")
            sys.exit(1)

        # === Slider venster voor nauwkeurigheid (percentage punten)
        try:
            slider_window = tk.Toplevel()
            slider_window.title("Kies nauwkeurigheid / aantal punten")
            
            label_var = tk.StringVar()
            label = tk.Label(slider_window, textvariable=label_var)
            label.pack(pady=10)
            
            percent_var = tk.IntVar(value=100)
            slider = tk.Scale(slider_window, from_=1, to=100, orient="horizontal", variable=percent_var)
            slider.pack(padx=20)
            
            def update_label(val):
                try:
                    pct = int(val)
                    num_sample = int((pct / 100) * num_total)
                    estimated_seconds = max(1, int(num_sample / 100000 * 10))  # Avoid 0 seconds
                    hrs, rem = divmod(estimated_seconds, 3600)
                    mins, secs = divmod(rem, 60)
                    
                    memory_mb = (num_sample * 64) / (1024 * 1024)  # More accurate estimate for processing
                    
                    label_text = f"{pct}% van {num_total:,} punten → {num_sample:,} punten\nGeschatte tijd: {hrs}h {mins}m {secs}s"
                    if memory_mb > 1000:
                        label_text += f"\nGeheugen: ~{memory_mb:.0f} MB"
                        
                    label_var.set(label_text)
                except Exception as e:
                    print(f"Fout in update_label: {e}")
            
            slider.config(command=update_label)
            update_label(percent_var.get())
            
            def confirm():
                slider_window.destroy()
            
            btn = tk.Button(slider_window, text="Bevestig", command=confirm)
            btn.pack(pady=10)
            slider_window.wait_window()
            sample_percent = percent_var.get()
            
        except Exception as e:
            show_error("GUI Fout", f"Probleem met het nauwkeurigheidsvenster:\n{str(e)}")
            sample_percent = 100  # Use default value

        # === Downsampling van target points
        try:
            num_sample = int((sample_percent / 100) * num_total)
            if num_sample <= 0:
                show_error("Ongeldige selectie", "Het aantal geselecteerde punten moet groter zijn dan 0.")
                sys.exit(1)
                
            print(f"🎯 Selecteer {num_sample:,} punten ({sample_percent}%) voor kleuroverdracht...")
            
            if num_sample < num_total:
                tgt_indices = np.random.choice(num_total, num_sample, replace=False)
                tgt_xyz = tgt_xyz_full[tgt_indices]
            else:
                tgt_indices = np.arange(num_total)
                tgt_xyz = tgt_xyz_full
                
            print(f"✅ Puntselectie voltooid")
            
        except MemoryError:
            show_error("Geheugen probleem", f"Onvoldoende geheugen om {num_sample:,} punten te verwerken.\n\nProbeer een lager percentage te kiezen.")
            sys.exit(1)
        except Exception as e:
            show_error("Fout bij puntselectie", f"Onverwachte fout bij het selecteren van punten:\n{str(e)}")
            sys.exit(1)

        # === Laad source punten
        try:
            print("📥 Lees bronbestand (met kleur)...")
            source_las = laspy.read(source_path)
            src_xyz = np.vstack((source_las.x, source_las.y, source_las.z)).T
            
            # Check if source file has color information
            if not hasattr(source_las, 'red') or not hasattr(source_las, 'green') or not hasattr(source_las, 'blue'):
                show_error("Geen kleurinformatie", "Het bronbestand bevat geen RGB kleurinformatie.\n\nZorg ervoor dat je een gekleurd LAS bestand selecteert.")
                sys.exit(1)
            
            src_rgb = np.vstack((source_las.red, source_las.green, source_las.blue)).T // 256
            src_points = len(src_xyz)
            
            if src_points == 0:
                show_error("Leeg bronbestand", "Het bronbestand bevat geen punten.")
                sys.exit(1)
                
            print(f"✅ Bronbestand geladen: {src_points:,} punten met kleurinformatie")
            
            # Check if coordinate systems are roughly compatible
            tgt_bounds = [(tgt_xyz_full[:, i].min(), tgt_xyz_full[:, i].max()) for i in range(3)]
            src_bounds = [(src_xyz[:, i].min(), src_xyz[:, i].max()) for i in range(3)]
            
            # Simple overlap check
            overlapping = True
            for i in range(3):
                if tgt_bounds[i][1] < src_bounds[i][0] or tgt_bounds[i][0] > src_bounds[i][1]:
                    overlapping = False
                    break
            
            if not overlapping:
                print("⚠️  Waarschuwing: De coördinaatgebieden van de bestanden overlappen niet.")
                print("   Dit kan resulteren in slechte kleuroverdracht.")
                print(f"   Doel bereik: X:{tgt_bounds[0]}, Y:{tgt_bounds[1]}, Z:{tgt_bounds[2]}")
                print(f"   Bron bereik: X:{src_bounds[0]}, Y:{src_bounds[1]}, Z:{src_bounds[2]}")
                
        except FileNotFoundError:
            show_error("Bestand niet gevonden", f"Het bronbestand kan niet worden gevonden: {source_path}")
            sys.exit(1)
        except MemoryError:
            show_error("Onvoldoende geheugen", f"Het bronbestand is te groot om in het geheugen te laden ({src_points:,} punten).\n\nProbeer een kleiner bronbestand te gebruiken.")
            sys.exit(1)
        except Exception as e:
            show_error("Fout bij laden bronbestand", f"Onverwachte fout bij het lezen van het bronbestand:\n{str(e)}\n\nControleer of het bestand niet beschadigd is en RGB kleuren bevat.")
            sys.exit(1)

        # === Zoek dichtstbijzijnde kleuren
        try:
            print("🔍 Bouw zoekstructuur voor nearest neighbor matching...")
            tree = cKDTree(src_xyz)
            
            print("🎨 Initialiseer kleurenarrays...")
            r_full = np.zeros(num_total, dtype=np.uint16)
            g_full = np.zeros(num_total, dtype=np.uint16) 
            b_full = np.zeros(num_total, dtype=np.uint16)
            
            print(f"🔄 Start kleuroverdracht voor {len(tgt_indices):,} punten...")
            
            for i, idx in enumerate(tqdm(tgt_indices, desc="🎨 Overdracht", unit="punt")):
                try:
                    tgt_pt = tgt_xyz_full[idx]
                    dist, nearest_idx = tree.query(tgt_pt)
                    
                    # Check if distance is reasonable (not too far)
                    if dist > 10.0:  # 10 meter threshold - adjust as needed
                        print(f"⚠️  Punt {i}: Grote afstand ({dist:.2f}m) tot dichtstbijzijnde punt")
                    
                    r, g, b = src_rgb[nearest_idx]
                    r_full[idx] = r * 256
                    g_full[idx] = g * 256
                    b_full[idx] = b * 256
                    
                except Exception as e:
                    print(f"❌ Fout bij punt {i} (index {idx}): {str(e)}")
                    # Continue with next point rather than crashing
                    continue
            
            print("✅ Kleuroverdracht voltooid")
            
        except MemoryError:
            show_error("Geheugen probleem", f"Onvoldoende geheugen voor kleuroverdracht.\n\nProbeer:\n- Een lager percentage punten te kiezen\n- Een kleiner bronbestand te gebruiken")
            sys.exit(1)
        except Exception as e:
            show_error("Fout bij kleuroverdracht", f"Onverwachte fout tijdens kleuroverdracht:\n{str(e)}\n\n{traceback.format_exc()}")
            sys.exit(1)

        # === Schrijf nieuwe LAS
        try:
            print(f"💾 Schrijf output naar {output_path}")
            
            # Create new LAS file with same format as target
            new_las = laspy.create(point_format=target_las.header.point_format, file_version=target_las.header.version)
            
            # Copy coordinates from target
            new_las.x = target_las.x
            new_las.y = target_las.y 
            new_las.z = target_las.z
            
            # Add transferred colors
            new_las.red = r_full
            new_las.green = g_full
            new_las.blue = b_full
            
            # Copy other attributes if they exist
            if hasattr(target_las, 'intensity'):
                new_las.intensity = target_las.intensity
            if hasattr(target_las, 'return_number'):
                new_las.return_number = target_las.return_number
            if hasattr(target_las, 'number_of_returns'):
                new_las.number_of_returns = target_las.number_of_returns
            if hasattr(target_las, 'classification'):
                new_las.classification = target_las.classification
            
            # Write the file
            new_las.write(output_path)
            
            # Verify the file was written successfully
            if not os.path.exists(output_path):
                raise FileNotFoundError("Output bestand werd niet aangemaakt")
                
            output_size = os.path.getsize(output_path)
            if output_size == 0:
                raise ValueError("Output bestand is leeg")
            
            print("✅ Klaar: kleuren overgezet naar gekozen outputbestand")
            print(f"📊 Bestand informatie:")
            print(f"   - Locatie: {output_path}")
            print(f"   - Grootte: {output_size / (1024*1024):.1f} MB")
            print(f"   - Aantal punten: {num_total:,}")
            print(f"   - Punten met kleur: {len(tgt_indices):,} ({sample_percent}%)")
            print("ℹ️  De gegenereerde .las file kan nu verder verwerkt worden in tools zoals CloudCompare.")
            
            # Show success dialog
            show_info("Succes!", f"Kleuroverdracht voltooid!\n\nOutput: {os.path.basename(output_path)}\nPunten: {num_total:,}\nKleuren toegepast: {len(tgt_indices):,} ({sample_percent}%)")
            
        except PermissionError:
            show_error("Toegang geweigerd", f"Geen toestemming om te schrijven naar:\n{output_path}\n\nControleer of:\n- Het bestand niet geopend is in een ander programma\n- Je schrijfrechten hebt voor de folder")
            sys.exit(1)
        except IOError as e:
            show_error("Bestand I/O fout", f"Fout bij schrijven van output bestand:\n{str(e)}\n\nMogelijke oorzaken:\n- Onvoldoende schijfruimte\n- Bestand is vergrendeld door ander programma")
            sys.exit(1)
        except Exception as e:
            show_error("Fout bij opslaan", f"Onverwachte fout bij het opslaan van het resultaat:\n{str(e)}\n\n{traceback.format_exc()}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Proces onderbroken door gebruiker")
        sys.exit(1)
    except Exception as e:
        show_error("Kritieke fout", f"Er is een onverwachte fout opgetreden:\n{str(e)}\n\nVolledige foutmelding:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()