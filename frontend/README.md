# Pratiko frontend

React 19 arayüzü Vite ile derlenir ve Vitest ile test edilir. Node.js 22.13+ (22.x veya 24 LTS) kullanın.

```powershell
npm ci
npm start
npm test
npm run build
npm audit
```

Geliştirme arayüzü `http://localhost:3000`, varsayılan API `http://localhost:5000` adresindedir. Başka bir API adresi için başlatmadan veya build almadan önce `REACT_APP_API_URL` değerini ayarlayın. Vite derleme çıktısı `build/` klasöründedir. Google Maps anahtarı backend yapılandırmasında kalır.

[Proje kurulumu, veri kaynakları ve sınırlar](../README.md)
