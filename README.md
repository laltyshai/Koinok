# 👗 E-Wardrobe (Digital Closet)

**E-Wardrobe** is a cross-platform mobile application designed to digitize, organize, and smartly plan your personal wardrobe. Built on the Flutter framework with a dedicated backend architecture, this project is heavily optimized to run seamlessly within cloud free-tier limits. It is designed to be a practical, daily-use tool for managing clothes and creating outfits efficiently.

The project solves the classic "full closet but nothing to wear" dilemma by helping users rediscover forgotten clothes, assemble outfit capsules (Looks), and track clothing wear frequency over time.

---

## ✨ Features

1. **Authentication & Security:** Full registration and login flow (Email/Password). Each user has an isolated, private cloud storage container to keep their wardrobe secure and personal.
2. **Wardrobe Digitization:** Easily upload clothing items categorized by type (*pants, shorts, t-shirts, accessories, etc.*) along with a photo and customizable metadata (color, season, isOversize, recommended temperature range, and activity tags like *sporty, theatre, official, home*).
3. **Wear Tracking (Smart Calendar):** An integrated calendar interface allows users to log what they wore each day. If a piece of clothing hasn't been worn for **10+ days**, the application automatically labels it as *"Suggested"*, helping users utilize their entire closet.
4. **Smart Dashboards:** A dedicated section displaying "forgotten" items alongside a randomized outfit generator to provide quick daily inspiration.
5. **Advanced Filtering:** Instant, multi-criteria search allowing users to filter their digital closet by color, last worn date, category, ideal temperature, or specific activity.
6. **Look Creator (Collections):** Users can group individual items into full outfits (e.g., *Pink Shirt + Denim Jeans*), name the combination (e.g., *Casual Summer*), and save them into a dedicated Looks gallery.
7. **Manual Matchmaking:** Ability to manually link matching clothes together. For example, you can explicitly add *pink shorts* to the "matching items" list of a *pink shirt*.
8. **Notes & Favorites:** A personal text-note feature for each clothing item, and a dedicated screen to quickly view all "liked" or favorite items.

---

## 🛠 Tech Stack

### Frontend (Mobile Application)
* **Framework:** Flutter (Dart)
* **State Management:** Riverpod (utilizing a modular architecture to manage complex filtering states and authentication cycles)
* **Networking:** Dio (custom client equipped with interceptors for seamless authorization token handling)
* **Image Processing:** `image_picker` + `flutter_image_compress` (client-side compression scaling down images to ~100-200 KB *before* uploading, severely minimizing cloud storage footprints)
* **UI Utilities:** `table_calendar` for historical wear tracking, and `cached_network_image` for smooth image caching and grid scrolling performance.

### Backend & Cloud Storage
* **Database:** Cloud Firestore / Custom DB (optimized document-oriented schema layout supporting offline caching mechanisms)
* **Storage:** Firebase Storage (structured file directory organized by `images/{userId}/{clothId}.jpg`)
* **Auth:** Firebase Authentication / Secure Token Service

---

## 📦 Database Schema Model

The system operates around three core data entities:

* `Cloth`: Holds the item ID, owner's userId, image URL, category, an array of historical wear timestamps (`lastWornDates`), an array of manually linked clothing IDs (`matchingClothIds`), an `isLiked` boolean flag, individual notes, and various metadata tags.
* `Look`: Connects an outfit ID and a custom name with an array of corresponding `clothIds` to represent a full appearance set.
* `User`: A basic profile holding the user's name, email, and account creation metadata mapped to a unique UI session.

---

## 🚀 Getting Started

### Step 1: Clone the Repository
```bash
git clone [https://github.com/your-username/e-wardrobe.git](https://github.com/your-username/e-wardrobe.git)
cd e-wardrobe