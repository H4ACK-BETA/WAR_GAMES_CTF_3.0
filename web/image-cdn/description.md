# 1m4g3::cdn

**Category:** Web  
**Difficulty:** Medium-Hard  
**Points:** 350  
**Author:** H3xPh4r04h  
**Flag Format:** `warCTF{...}`  
**Port:** 8080  

---

> *"Upload your images. We'll optimize them. Totally safe. We use ImageMagick."*

CloudPix built a blazing-fast image CDN. Upload, optimize, serve. PNG, JPG, GIF, WebP - all supported.

Oh, and SVG too. Because SVG is just an image format, right? Nothing dangerous about XML with embedded references to arbitrary URLs...

Their engineers assure us the processing pipeline is completely secure. The policy file says "allow all." What could go wrong?

## Hints

1. What image formats does the CDN accept? Are all of them equally safe?
2. SVG is just XML. What can XML reference?
3. Not all services are meant to be public. Some only listen internally.
4. The admin panel exists, but you'll need credentials to get in.

## Connection

```
http://<host>:8080
```
