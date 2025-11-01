from django.db import models


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.TextField(unique=True)
    password_hash = models.TextField()
    role = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    username = models.TextField(null=True, blank=True)
    profile_picture = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    date_joined = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'users'

    def __str__(self):
        return self.username or self.email


class Category(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    category_name = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False

        db_table = 'categories'

    def __str__(self):
        return self.category_name


class Course(models.Model):
    course_id = models.BigAutoField(primary_key=True)
    course_code = models.TextField()
    course_name = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'courses'

    def __str__(self):
        return self.course_name


class Resource(models.Model):
    resource_id = models.BigAutoField(primary_key=True)
    title = models.TextField()
    type = models.TextField()
    resource_location = models.TextField()
    upload_date = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'resources'

    def __str__(self):
        return self.title


class Post(models.Model):
    post_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    post_type = models.TextField()
    description = models.CharField(max_length=255, null=True, blank=True)
    upvote_count = models.IntegerField(default=0)
    downvote_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'posts'

    def __str__(self):
        return self.title or f"Post {self.post_id}"


class Comment(models.Model):
    comment_id = models.BigAutoField(primary_key=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'comments'

    def __str__(self):
        return f"Comment {self.comment_id}"


class PostVote(models.Model):
    vote_id = models.BigAutoField(primary_key=True)
    vote_type = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        managed = False

        db_table = 'post_votes'
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.vote_type} by {self.user}"


class SearchHistory(models.Model):
    search_id = models.BigAutoField(primary_key=True)
    search_term = models.TextField()
    search_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'search_history'

    def __str__(self):
        return self.search_term


class PasswordRecovery(models.Model):
    token_id = models.BigAutoField(primary_key=True)
    reset_token = models.TextField()
    expiration_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'password_recovery'

    def __str__(self):
        return f"PasswordResetToken({self.user})"


class ProfileSettings(models.Model):
    setting_id = models.BigAutoField(primary_key=True)
    theme_preference = models.TextField(default='light')
    notification_preference = models.TextField(default='all')
    language = models.TextField(default='en')
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        managed = False

        db_table = 'profile_settings'

    def __str__(self):
        return f"Settings for {self.user}"
