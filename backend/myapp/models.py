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
    is_forum = models.BooleanField(default=False)
    best_answer_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default='open')

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


class ViolationType(models.Model):
    """Predefined violation types for reporting system"""
    violation_id = models.BigAutoField(primary_key=True)
    name = models.TextField(unique=True)  # e.g., "inappropriate_content", "harassment"
    display_name = models.TextField()  # e.g., "Inappropriate Content", "Harassment"
    description = models.TextField(null=True, blank=True)
    severity_level = models.IntegerField(default=1)  # 1=low, 2=medium, 3=high
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'violation_types'

    def __str__(self):
        return self.display_name


class PostReport(models.Model):
    """Reports submitted by users against posts"""
    report_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='filed_reports')
    violation_type = models.ForeignKey(ViolationType, on_delete=models.SET_NULL, null=True)
    details = models.TextField(null=True, blank=True)  # Optional additional details
    status = models.TextField(
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('under_review', 'Under Review'),
            ('resolved', 'Resolved'),
            ('dismissed', 'Dismissed'),
            ('action_taken', 'Action Taken')
        ]
    )
    admin_notes = models.TextField(null=True, blank=True)  # For moderator/admin use
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_reports'
    )

    class Meta:
        managed = False
        db_table = 'post_reports'
        unique_together = ('post', 'reporter')  # One report per user per post

    def __str__(self):
        return f"Report by {self.reporter} on Post {self.post.post_id}"


class CommentReport(models.Model):
    """Reports submitted by users against comments"""
    report_id = models.BigAutoField(primary_key=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_reports')
    violation_type = models.ForeignKey(ViolationType, on_delete=models.SET_NULL, null=True)
    details = models.TextField(null=True, blank=True)
    status = models.TextField(
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('under_review', 'Under Review'),
            ('resolved', 'Resolved'),
            ('dismissed', 'Dismissed'),
            ('action_taken', 'Action Taken')
        ]
    )
    admin_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_comment_reports'
    )

    class Meta:
        managed = False
        db_table = 'comment_reports'
        unique_together = ('comment', 'reporter')

    def __str__(self):
        return f"Report by {self.reporter} on Comment {self.comment.comment_id}"
