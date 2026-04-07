# Final_dbs - Vercel + Blob Ready

This version is prepared for:
- Django on Vercel
- PostgreSQL via a provider like Neon
- Product image upload with Vercel Blob

## Important environment variables
- `DJANGO_SECRET`
- `DATABASE_URL`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `BLOB_READ_WRITE_TOKEN`

## Build command on Vercel
```bash
bash build_vercel.sh
```

## After deployment
Run migrations from your local machine against the same production database:
```bash
python manage.py migrate
python manage.py seed_inventory
```

## Demo admin
- `admin@example.com`
- `Admin@123`
