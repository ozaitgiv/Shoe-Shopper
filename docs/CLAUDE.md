# Shoe-Shopper Project Architecture

## Project Overview
Shoe-Shopper is a full-stack web application that helps users find the perfect shoe fit by analyzing foot measurements from uploaded images. The system uses computer vision to measure foot dimensions and provides intelligent shoe recommendations based on a 4D scoring algorithm.

## Technology Stack

### Backend (Django REST API)
- **Framework**: Django 5.2.4 with Django REST Framework 3.16.0
- **Database**: PostgreSQL (production) / SQLite3 (development)
- **Image Processing**: OpenCV + Roboflow inference SDK
- **Authentication**: Token-based authentication + session-based guest support
- **Deployment**: Railway/Render with WhiteNoise for static files

### Frontend (Next.js)
- **Framework**: Next.js 15.3.4 with React 19
- **Language**: TypeScript 5
- **Styling**: TailwindCSS 4
- **Build Tool**: Turbopack
- **Icons**: Lucide React

### Computer Vision
- **Provider**: Roboflow inference workflows
- **Foot Detection**: Bounding box + polygon segmentation
- **Paper Reference**: Letter/A4 paper for scale calibration
- **Measurements**: Length, width, area, perimeter (4D analysis)

## Project Structure

```
Shoe-Shopper/
├── backend/                    # Django REST API
│   ├── core/                  # Main Django app
│   │   ├── models.py         # Data models (FootImage, Shoe, GuestSession)
│   │   ├── views.py          # API endpoints and business logic
│   │   ├── serializers.py    # DRF serializers
│   │   ├── urls.py           # URL routing
│   │   ├── score_shoes.py    # 4D recommendation algorithm
│   │   ├── tests/            # Comprehensive test suite
│   │   └── migrations/       # Database migrations
│   ├── shoe_shopper/         # Django project settings
│   ├── media/                # Uploaded images (foot_images, insole_images)
│   ├── requirements.txt      # Python dependencies
│   └── manage.py            # Django management
├── frontend/                 # Next.js client
│   ├── src/app/             # App Router pages
│   │   ├── page.tsx         # Home page
│   │   ├── upload/          # Foot measurement upload
│   │   ├── recommendations/ # Shoe recommendations
│   │   └── account/         # User account management
│   ├── public/              # Static assets
│   └── package.json         # Node dependencies
├── cv/                      # Computer vision utilities
└── docker-compose.yml       # Local PostgreSQL setup
```

## Database Models

### FootImage
**Purpose**: Stores uploaded foot images and extracted measurements
- `user`: FK to User (nullable for guests)
- `guest_session`: FK to GuestSession (UUID-based guest tracking)
- `image`: ImageField for uploaded foot photo
- `status`: 'processing', 'complete', 'error'
- `length_inches`, `width_inches`: Basic dimensions
- `area_sqin`, `perimeter_inches`: Advanced 4D measurements
- `error_message`: Processing error details

### Shoe
**Purpose**: Product catalog with insole measurements
- `company`, `model`: Shoe identification
- `us_size`, `width_category`, `gender`: Size specifications
- `function`: 'casual', 'hiking', 'work', 'running'
- `price_usd`, `product_url`: Commerce data
- `shoe_image_url`: Product image URL
- `insole_image`: Uploaded insole photo for measurement
- `insole_length`, `insole_width`, `insole_area`, `insole_perimeter`: Measured dimensions

### GuestSession
**Purpose**: UUID-based session tracking for guest users
- `id`: Primary UUID key
- `created_at`, `last_accessed`: Timestamps
- `is_expired()`: 1-hour expiration check
- `cleanup_expired()`: Batch cleanup utility

## API Endpoints

### Authentication
- `POST /api/auth/signup/` - User registration
- `POST /api/auth/login/` - Token authentication
- `POST /api/auth/logout/` - Session cleanup
- `GET /api/auth/user/` - User profile
- `DELETE /api/auth/account/` - Account deletion

### Measurements
- `POST /api/measurements/upload/` - Upload foot image
- `GET /api/measurements/<id>/` - Check processing status
- `GET /api/measurements/latest/` - Get latest measurement

### Recommendations
- `GET /api/recommendations/` - Get personalized shoe recommendations
- `GET /api/shoes/` - List all shoes with fit scores

### Utilities
- `GET /api/csrf/` - CSRF token for frontend

## 4D Scoring Algorithm

### Core Components
**Location**: `backend/core/views.py` in `enhanced_score_shoe_4d()`

### Scoring Dimensions (Research-Based Weights)
1. **Length (37.5%)**: Most critical for comfort and safety
2. **Width (27.5%)**: Critical for comfort and foot health  
3. **Perimeter (22.5%)**: Accounts for foot circumference variations
4. **Area (12.5%)**: Accounts for overall foot volume

### Fit Thresholds
- **Excellent (85+)**: Perfect fit with proper toe room
- **Good (65+)**: Good fit with adequate comfort
- **Fair (45+)**: Acceptable fit, may need consideration
- **Poor (<45)**: Poor fit, not recommended

### Key Improvements Over Legacy Algorithm
- Smooth penalty curves instead of harsh binary thresholds
- Extended tolerance zones (10% width difference = 70 score vs 0)
- Gradual length penalties (2% tight = 80+ score vs severe penalty)
- No sudden score drops for minor measurement variations
- Better handling of None values with estimation fallbacks

### Shoe-Type Specific Clearances
- **Running**: Extra toe room (0.5") and width (0.08")
- **Hiking**: Maximum clearances (0.6" length, 0.12" width)
- **Casual**: Minimal clearances (0.25" length, 0.04" width)
- **Work**: Moderate clearances (0.4" length, 0.08" width)

## Computer Vision Pipeline

### Workflow Integration
1. **Primary**: Polygon segmentation workflow for real area/perimeter
2. **Fallback**: Bounding box detection with area/perimeter estimation
3. **Scale Reference**: Paper detection (Letter 8.5" or A4 8.27" width)

### Measurement Process
1. Upload foot image with paper reference
2. Roboflow inference detects foot and paper polygons
3. Calculate pixels-per-inch from paper width
4. Extract bounding box dimensions (length/width)
5. Calculate real polygon area/perimeter using Shoelace formula
6. Convert all measurements to inches

### Error Handling
- Paper not detected → Specific error message
- Foot not detected → Specific error message  
- Processing failures → Graceful fallback to estimation

## Guest User System

### Session Management
- **New System**: UUID-based `GuestSession` model (1-hour expiration)
- **Legacy Support**: Django session keys (7-day retention for compatibility)
- **Frontend Integration**: `X-Guest-Session-ID` header
- **Cleanup**: Automatic expired session removal (10% random trigger)

### Data Isolation
- Each guest session has isolated foot measurements
- No cross-contamination between concurrent guests
- Session validation prevents unauthorized access

## Testing Suite

### Test Coverage
**Location**: `backend/core/tests/`

### Test Categories
- **Models**: `test_models.py` - Model validation and methods
- **Views**: `test_views.py`, `test_views_strategic.py` - API endpoint testing
- **API Endpoints**: `test_api_endpoints.py` - Full API integration
- **Image Processing**: `test_image_processing.py` - Computer vision pipeline
- **Scoring Algorithm**: `test_score_shoes.py`, `test_penalty_functions.py`
- **Performance**: `test_performance.py` - Load and stress testing
- **E2E**: `test_e2e.py` - End-to-end user workflows
- **Edge Cases**: `test_edge_cases.py` - Error handling and boundary conditions

### Test Framework
- **Django**: Built-in TestCase and TransactionTestCase
- **pytest**: Alternative test runner with fixtures
- **Coverage**: HTML coverage reports in `htmlcov/`
- **Factory Boy**: Test data generation
- **Selenium**: Frontend integration testing

### Running Tests
```bash
# All tests with coverage
python run_all_tests.py

# Specific test categories
python manage.py test core.tests.test_models
python manage.py test core.tests.test_views

# Coverage report
coverage run --source='.' manage.py test
coverage html
```

## Configuration & Environment

### Environment Variables
```bash
# Required for production
DJANGO_SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db
ROBOFLOW_API_KEY=your_roboflow_key

# Optional
DEBUG=False
RAILWAY_ENVIRONMENT=production  # For Railway deployment
RENDER=1                        # For Render deployment
```

### Settings Structure
**Location**: `backend/shoe_shopper/settings.py`

### Environment Detection
- **Railway**: `RAILWAY_ENVIRONMENT` environment variable
- **Render**: `RENDER` environment variable  
- **Local**: Default development settings

### Database Configuration
- **Production**: PostgreSQL via `DATABASE_URL`
- **Development**: SQLite3 (`db.sqlite3`)

### Static Files
- **Production**: WhiteNoise with compression
- **Development**: Standard Django static files
- **Media**: Local filesystem (future: AWS S3)

### CORS & Security
- **CORS**: Configured for cross-origin frontend requests
- **CSRF**: Custom headers supported (`X-CSRFToken`, `X-Guest-Session-ID`)
- **Authentication**: Token + Session dual support

## Development Commands

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Load sample shoe data
python load_shoes.py

# Run server
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Development server
npm run build  # Production build
```

### Database Operations
```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset migrations (development only)
python reset_migrations.py

# Database shell
python manage.py dbshell
```

### Testing & Quality
```bash
# Run all tests with coverage
python run_all_tests.py

# Specific test suites
python manage.py test core.tests.test_scoring
python manage.py test core.tests.test_api_endpoints

# Code analysis
python analyze_algorithm.py
python analyze_penalties.py
```

## Deployment Architecture

### Production Environment
- **Backend**: Railway/Render with PostgreSQL
- **Frontend**: Vercel (recommended) or Railway
- **Static Files**: WhiteNoise compression + CDN
- **Media Files**: Local filesystem (future: AWS S3)
- **SSL**: Automatic via platform providers

### Environment-Specific Settings
- **CORS**: Configured for production domains
- **CSRF**: Secure cookie settings for cross-site requests
- **Database**: Connection pooling with health checks
- **Logging**: Structured logging to console for platform log aggregation

## Performance & Monitoring

### Database Optimization
- **Indexes**: Created on frequently queried fields
- **Connection Pooling**: Enabled for production
- **Query Optimization**: Select_related and prefetch_related used appropriately

### Image Processing
- **Caching**: Roboflow inference caching enabled
- **Error Handling**: Graceful fallbacks for API failures
- **Async Processing**: Image processing in upload endpoint

### Session Management
- **Cleanup**: Automatic cleanup of expired sessions
- **Isolation**: Proper data isolation between users/guests
- **Performance**: UUID-based sessions for better concurrency

## Security Considerations

### Authentication & Authorization
- **Token Authentication**: Secure API access for authenticated users
- **Guest Sessions**: Isolated data access without authentication
- **CSRF Protection**: Enabled for state-changing operations
- **Session Security**: Secure cookie settings in production

### Input Validation
- **Image Upload**: File type and size validation
- **API Input**: Serializer validation on all endpoints  
- **SQL Injection**: Django ORM protection
- **XSS Prevention**: DRF serialization handles escaping

### Data Privacy
- **Guest Data**: Automatic cleanup after 1-7 days
- **User Data**: Cascade deletion when user account deleted
- **Image Storage**: Local filesystem with proper permissions
- **Logging**: No sensitive data in logs

## Common Development Patterns

### Adding New API Endpoints
1. Define URL pattern in `core/urls.py`
2. Implement view in `core/views.py`
3. Add serializer if needed in `core/serializers.py`
4. Write tests in appropriate `core/tests/test_*.py` file
5. Update this documentation

### Database Schema Changes
1. Modify models in `core/models.py`
2. Generate migration: `python manage.py makemigrations`
3. Review migration file for correctness
4. Test migration: `python manage.py migrate`
5. Update any affected serializers/views
6. Add/update tests for model changes

### Algorithm Updates
1. Modify scoring functions in `core/views.py`
2. Update constants and thresholds as needed
3. Run penalty analysis: `python analyze_penalties.py`
4. Add comprehensive tests in `core/tests/test_scoring.py`
5. Update fit thresholds if category boundaries change

## Troubleshooting

### Common Issues

**Image Processing Fails**
- Check `ROBOFLOW_API_KEY` environment variable
- Verify internet connectivity for API calls
- Check image format and size (should be reasonable dimensions)
- Review error messages in FootImage.error_message field

**Database Connection Issues**
- Verify `DATABASE_URL` format for production
- Check PostgreSQL container status for local development: `docker-compose up postgres`
- Run migrations if schema is out of sync: `python manage.py migrate`

**CSRF/CORS Errors** 
- Verify frontend URL in `CORS_ALLOWED_ORIGINS`
- Check `CSRF_TRUSTED_ORIGINS` includes frontend domain
- Ensure CSRF token is included in requests

**Guest Session Issues**
- Check `X-Guest-Session-ID` header is being sent
- Verify UUID format of session ID
- Check session expiration (1 hour limit)
- Review session cleanup logs

### Development Tools

**Database Inspection**
```bash
python manage.py shell
>>> from core.models import FootImage, Shoe, GuestSession
>>> FootImage.objects.count()
>>> Shoe.objects.filter(is_active=True).count()
```

**Manual Image Processing Test**
```bash
python manage.py shell
>>> from core.views import process_foot_image_enhanced
>>> result = process_foot_image_enhanced('/path/to/image.jpg')
>>> print(result)
```

**Session Cleanup**
```bash
python manage.py shell
>>> from core.views import cleanup_old_guest_sessions
>>> cleanup_old_guest_sessions()
```

## Code Review Guidelines

### Overview
Code reviews are critical for maintaining code quality, security, and reliability in the Shoe-Shopper project. Every pull request must undergo thorough review before merging to ensure adherence to project standards.

### Review Process

#### 1. Pre-Review Checklist (Author)
Before requesting a review, ensure:
- [ ] All tests pass locally (`python run_all_tests.py`)
- [ ] Code follows project conventions and style
- [ ] No sensitive data (API keys, passwords) in commits
- [ ] Proper error handling implemented
- [ ] Documentation updated if needed
- [ ] Self-review completed

#### 2. Review Assignment
- **Backend Changes**: Require senior backend developer approval
- **Frontend Changes**: Require frontend-familiar reviewer
- **Algorithm Changes**: Require ML/algorithm expertise review
- **Security Changes**: Require security-focused review
- **Database Changes**: Require database expert review

#### 3. Review Workflow
1. **Automated Checks**: CI/CD pipeline must pass
2. **Manual Review**: Human reviewer examination
3. **Testing**: Reviewer tests functionality locally if significant
4. **Approval**: Explicit approval before merge
5. **Merge**: Squash commits to maintain clean history

### Quality Standards

#### Code Organization & Readability
**✅ Look For:**
- Clear, descriptive function/variable names
- Proper separation of concerns
- Consistent code formatting
- Logical file organization
- Appropriate comments explaining complex logic

**❌ Red Flags:**
```python
# Bad: Unclear function name and magic numbers
def calc(x, y):
    return x * 0.375 + y * 0.275

# Good: Clear purpose and named constants
def calculate_fit_score(length_score, width_score):
    LENGTH_WEIGHT = 0.375
    WIDTH_WEIGHT = 0.275
    return length_score * LENGTH_WEIGHT + width_score * WIDTH_WEIGHT
```

#### Error Handling
**✅ Required Patterns:**
```python
# API endpoints must handle exceptions
@api_view(['POST'])
def upload_foot_image(request):
    try:
        # Processing logic
        result = process_image(image_path)
        return Response(result)
    except ValidationError as e:
        logger.warning("Validation failed", extra={'error': str(e)})
        return Response({'error': 'Invalid input'}, status=400)
    except Exception as e:
        logger.exception("Unexpected error in upload")
        return Response({'error': 'Server error'}, status=500)
```

**❌ Avoid:**
- Bare `except:` clauses
- Swallowing exceptions without logging
- Exposing internal error details to users

#### Database Operations
**✅ Best Practices:**
```python
# Use select_related for FK relationships
shoes = Shoe.objects.select_related('category').filter(is_active=True)

# Use get_or_404 for single object retrieval
shoe = get_object_or_404(Shoe, pk=shoe_id, is_active=True)

# Use transactions for multiple related operations
from django.db import transaction
@transaction.atomic
def create_shoe_with_measurements(shoe_data, measurements):
    shoe = Shoe.objects.create(**shoe_data)
    # Related operations...
```

**❌ Red Flags:**
- N+1 query problems
- Missing database indexes
- Raw SQL without parameterization
- Missing transaction boundaries

### Security Review Checklist

#### Authentication & Authorization
**✅ Verify:**
- [ ] Proper permission classes on all endpoints
- [ ] User can only access their own data
- [ ] Guest session isolation working correctly
- [ ] Token authentication properly implemented

```python
# Good: Proper authorization check
class FootImageDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        foot_image = get_object_or_404(FootImage, pk=pk)
        
        # Authorization check
        if foot_image.user and foot_image.user != request.user:
            return Response({'error': 'Access denied'}, status=403)
        # ... rest of logic
```

#### Input Validation
**✅ Required:**
- [ ] All user inputs validated through serializers
- [ ] File upload size and type restrictions
- [ ] SQL injection prevention (use ORM)
- [ ] XSS prevention (proper serialization)

```python
# Good: Proper input validation
class FootImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootImage
        fields = ['image', 'paper_size']
    
    def validate_image(self, value):
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("Image too large")
        if not value.content_type.startswith('image/'):
            raise serializers.ValidationError("Invalid file type")
        return value
```

#### Sensitive Data Protection
**❌ Never Allow:**
- API keys, passwords, secrets in code
- Sensitive data in logs
- Debug information exposed to production users
- Unencrypted sensitive data storage

**✅ Required:**
```python
# Good: Proper secret handling
ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY')
if not ROBOFLOW_API_KEY:
    raise ImproperlyConfigured("ROBOFLOW_API_KEY environment variable required")

# Good: Safe logging without sensitive data
logger.info("Image processing started", extra={
    'user_id': user.id if user else 'guest',
    'session_id': str(session.id)[:8] + '...',  # Truncated for privacy
    'image_size': image.size
})
```

#### CSRF & CORS Protection
**✅ Verify:**
- [ ] CSRF protection enabled for state-changing operations
- [ ] CORS properly configured for production domains
- [ ] No overly permissive CORS settings in production

### Testing Requirements

#### Test Coverage Standards
**Minimum Requirements:**
- [ ] **90%+ code coverage** for new code
- [ ] **Unit tests** for all business logic functions
- [ ] **Integration tests** for API endpoints
- [ ] **Edge case tests** for error conditions

#### Required Test Categories

**1. Model Tests (`test_models.py`)**
```python
class TestFootImage(TestCase):
    def test_str_representation(self):
        """Test FootImage string representation"""
        foot_image = FootImage.objects.create(...)
        expected = f"FootImage {foot_image.id} by {user.username}"
        self.assertEqual(str(foot_image), expected)
    
    def test_guest_session_isolation(self):
        """Test guest sessions are properly isolated"""
        # Test implementation...
```

**2. API Tests (`test_api_endpoints.py`)**
```python
class TestFootImageUpload(APITestCase):
    def test_upload_requires_valid_image(self):
        """Test upload rejects invalid files"""
        response = self.client.post('/api/measurements/upload/', {
            'image': 'not_an_image'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_guest_session_created(self):
        """Test guest session created for anonymous uploads"""
        # Test implementation...
```

**3. Algorithm Tests (`test_scoring.py`)**
```python
class TestScoringAlgorithm(TestCase):
    def test_perfect_fit_scores_high(self):
        """Test perfect fit receives excellent score"""
        score = enhanced_score_shoe_4d(
            user_length=10.0, user_width=3.6,
            user_area=27.0, user_perimeter=28.0,
            shoe_length=10.2, shoe_width=3.7,
            shoe_area=28.0, shoe_perimeter=29.0
        )
        self.assertGreaterEqual(score, 85)  # Excellent threshold
```

**4. Security Tests (`test_security.py`)**
```python
class TestSecurity(APITestCase):
    def test_user_cannot_access_other_measurements(self):
        """Test users cannot access other users' data"""
        other_user = User.objects.create_user('other', 'pass')
        other_foot_image = FootImage.objects.create(user=other_user, ...)
        
        response = self.client.get(f'/api/measurements/{other_foot_image.id}/')
        self.assertEqual(response.status_code, 403)
```

#### Performance Testing
**Required for:**
- Algorithm changes (test with realistic data volumes)
- Database query changes (check for N+1 problems)
- Image processing modifications (test with various image sizes)

```python
def test_recommendation_performance(self):
    """Test recommendations perform within acceptable time"""
    # Create 100 test shoes
    shoes = [Shoe.objects.create(...) for _ in range(100)]
    
    start_time = time.time()
    response = self.client.get('/api/recommendations/')
    duration = time.time() - start_time
    
    self.assertLess(duration, 2.0)  # Must complete within 2 seconds
    self.assertEqual(response.status_code, 200)
```

### Algorithm-Specific Review

#### Scoring Function Changes
**✅ Verify:**
- [ ] Algorithm changes backed by research/analysis
- [ ] No sudden score discontinuities
- [ ] Proper handling of edge cases (None values, extreme ratios)
- [ ] Performance impact assessed
- [ ] Backward compatibility considered

**Required Analysis:**
```python
# Must include analysis script results
python analyze_penalties.py  # Check penalty curves
python analyze_algorithm.py  # Validate scoring distribution
```

#### Computer Vision Changes
**✅ Review:**
- [ ] Error handling for API failures
- [ ] Graceful fallbacks for detection failures
- [ ] Proper measurement unit conversions
- [ ] Image processing security (file type validation)

### Database Migration Review

#### Migration Safety
**✅ Required Checks:**
- [ ] Migration is reversible (has reverse operation)
- [ ] No data loss risk
- [ ] Proper indexes added for new queries
- [ ] Large table migrations use appropriate strategy

```python
# Good: Reversible migration with proper indexes
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='footimage',
            name='processing_time',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_footimage_processing_time ON core_footimage (processing_time);",
            reverse_sql="DROP INDEX idx_footimage_processing_time;"
        ),
    ]
```

### Frontend Review (Next.js/TypeScript)

#### TypeScript Standards
**✅ Required:**
- [ ] Proper type definitions for all props/functions
- [ ] No `any` types without justification
- [ ] API response types defined
- [ ] Error state handling

```typescript
// Good: Proper typing
interface FootMeasurement {
  id: number;
  length_inches: number;
  width_inches: number;
  area_sqin?: number;
  perimeter_inches?: number;
  status: 'processing' | 'complete' | 'error';
}

async function uploadFootImage(file: File): Promise<FootMeasurement> {
  const formData = new FormData();
  formData.append('image', file);
  
  const response = await fetch('/api/measurements/upload/', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }
  
  return response.json();
}
```

#### React Best Practices
**✅ Verify:**
- [ ] Proper error boundaries
- [ ] Loading states handled
- [ ] No memory leaks (proper cleanup)
- [ ] Accessibility considerations (ARIA labels, keyboard navigation)

### Review Comments Guidelines

#### Effective Feedback
**✅ Good Comments:**
```
"Consider extracting this magic number into a named constant for clarity:
```python
EXCELLENT_FIT_THRESHOLD = 85
```

"This could cause an N+1 query problem. Consider using select_related():
```python
shoes = Shoe.objects.select_related('category').filter(is_active=True)
```

"Missing error handling for the case where the API returns 500. Should we show a user-friendly message?"
```

**❌ Avoid:**
- "This is wrong" (without explanation)
- Nitpicking style issues handled by linters
- Rewriting entire implementations in comments

#### Priority Levels
**🔴 Must Fix (Blocking):**
- Security vulnerabilities
- Data corruption risks  
- Breaking changes without proper migration
- Missing critical error handling

**🟡 Should Fix (Before Merge):**
- Performance issues
- Poor error messages
- Missing tests for new functionality
- Code clarity issues

**🟢 Consider (Nice to Have):**
- Code style improvements
- Performance optimizations
- Documentation enhancements

### Tools & Automation

#### Required Checks
```bash
# Must pass before merge
python run_all_tests.py              # All tests
python manage.py check              # Django system check
python -m flake8 core/              # Style checking
python -m bandit -r core/           # Security linting
```

#### Recommended IDE Setup
- **VS Code**: Python extension with Django support
- **PyCharm**: Django project configuration
- **Linting**: flake8, black, isort
- **Type Checking**: mypy (for critical components)

### Post-Merge Follow-up

#### Monitoring
- [ ] Check production logs for new errors
- [ ] Monitor performance metrics
- [ ] Verify deployment succeeded
- [ ] Test critical user flows

#### Rollback Plan
- [ ] Database migration rollback tested
- [ ] Feature flags available for quick disable
- [ ] Monitoring alerts configured
- [ ] Team notified of changes

---

## Future Development

### Planned Enhancements
- AWS S3 integration for media files
- Real-time image processing with WebSocket updates
- ML model for improved foot shape analysis
- Mobile app with camera integration
- Advanced filtering and search capabilities
- User preferences and favorites system

### Technical Debt
- Migrate from legacy session system to UUID-based fully
- Add comprehensive API documentation (OpenAPI/Swagger)
- Implement proper logging aggregation for production
- Add monitoring and alerting for critical failures
- Consider GraphQL for more efficient data fetching

---

*This documentation is maintained to provide comprehensive guidance for development and operations. Update when making significant architectural changes.*