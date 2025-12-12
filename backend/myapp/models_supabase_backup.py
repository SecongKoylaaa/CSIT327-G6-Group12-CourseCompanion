[
  {
    "json_agg": [
      {
        "table_name": "django_migrations",
        "columns": [
          {
            "column_name": "id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "app",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "name",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "applied",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "django_content_type",
        "columns": [
          {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "app_label",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "model",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "auth_permission",
        "columns": [
          {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "name",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "content_type_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "codename",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "auth_group",
        "columns": [
          {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "name",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "auth_group_permissions",
        "columns": [
          {
            "column_name": "id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "group_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "permission_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "auth_user",
        "columns": [
          {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "password",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "last_login",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "is_superuser",
            "data_type": "boolean",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "username",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "first_name",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "last_name",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "email",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "is_staff",
            "data_type": "boolean",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "is_active",
            "data_type": "boolean",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "date_joined",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "auth_user_groups",
        "columns": [
          {
            "column_name": "id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "group_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "auth_user_user_permissions",
        "columns": [
          {
            "column_name": "id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "permission_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "posts",
        "columns": [
          {
            "column_name": "post_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('posts_post_id_seq'::regclass)"
          },
          {
            "column_name": "content",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "post_type",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          },
          {
            "column_name": "updated_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "course_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "title",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "upvote_count",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": "0"
          },
          {
            "column_name": "downvote_count",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": "0"
          },
          {
            "column_name": "description",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "subject",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "is_forum",
            "data_type": "boolean",
            "is_nullable": "NO",
            "column_default": "false"
          },
          {
            "column_name": "best_answer_id",
            "data_type": "integer",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "status",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": "'open'::text"
          }
        ]
      },
      {
        "table_name": "django_admin_log",
        "columns": [
          {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "action_time",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "object_id",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "object_repr",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "action_flag",
            "data_type": "smallint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "change_message",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "content_type_id",
            "data_type": "integer",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "categories",
        "columns": [
          {
            "column_name": "category_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('categories_category_id_seq'::regclass)"
          },
          {
            "column_name": "category_name",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "description",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          }
        ]
      },
      {
        "table_name": "courses",
        "columns": [
          {
            "column_name": "course_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('courses_course_id_seq'::regclass)"
          },
          {
            "column_name": "course_code",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "course_name",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "description",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          },
          {
            "column_name": "updated_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "category_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "moderator_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "users",
        "columns": [
          {
            "column_name": "id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('users_id_seq'::regclass)"
          },
          {
            "column_name": "email",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "password_hash",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "role",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": "now()"
          },
          {
            "column_name": "username",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "profile_picture",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "bio",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "date_joined",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": "now()"
          },
          {
            "column_name": "last_login",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "instance_id",
            "data_type": "uuid",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "id",
            "data_type": "uuid",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "aud",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "role",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "email",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "encrypted_password",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "email_confirmed_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "invited_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "confirmation_token",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "confirmation_sent_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "recovery_token",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "recovery_sent_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "email_change_token_new",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "email_change",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "email_change_sent_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "last_sign_in_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "raw_app_meta_data",
            "data_type": "jsonb",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "raw_user_meta_data",
            "data_type": "jsonb",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "is_super_admin",
            "data_type": "boolean",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "updated_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "phone",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": "NULL::character varying"
          },
          {
            "column_name": "phone_confirmed_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "phone_change",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": "''::character varying"
          },
          {
            "column_name": "phone_change_token",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": "''::character varying"
          },
          {
            "column_name": "phone_change_sent_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "confirmed_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "email_change_token_current",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": "''::character varying"
          },
          {
            "column_name": "email_change_confirm_status",
            "data_type": "smallint",
            "is_nullable": "YES",
            "column_default": "0"
          },
          {
            "column_name": "banned_until",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "reauthentication_token",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": "''::character varying"
          },
          {
            "column_name": "reauthentication_sent_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "is_sso_user",
            "data_type": "boolean",
            "is_nullable": "NO",
            "column_default": "false"
          },
          {
            "column_name": "deleted_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "is_anonymous",
            "data_type": "boolean",
            "is_nullable": "NO",
            "column_default": "false"
          }
        ]
      },
      {
        "table_name": "resources",
        "columns": [
          {
            "column_name": "resource_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('resources_resource_id_seq'::regclass)"
          },
          {
            "column_name": "title",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "type",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "resource_location",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "upload_date",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          },
          {
            "column_name": "course_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "uploaded_by",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "comments",
        "columns": [
          {
            "column_name": "comment_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('comments_comment_id_seq'::regclass)"
          },
          {
            "column_name": "text",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          },
          {
            "column_name": "post_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "parent_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "edited",
            "data_type": "boolean",
            "is_nullable": "YES",
            "column_default": "false"
          },
          {
            "column_name": "upvote_count",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": "0"
          },
          {
            "column_name": "downvote_count",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": "0"
          }
        ]
      },
      {
        "table_name": "search_history",
        "columns": [
          {
            "column_name": "search_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('search_history_search_id_seq'::regclass)"
          },
          {
            "column_name": "search_term",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "search_date",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "password_recovery",
        "columns": [
          {
            "column_name": "token_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('password_recovery_token_id_seq'::regclass)"
          },
          {
            "column_name": "reset_token",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "expiration_time",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          }
        ]
      },
      {
        "table_name": "post_votes",
        "columns": [
          {
            "column_name": "vote_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('post_votes_vote_id_seq'::regclass)"
          },
          {
            "column_name": "post_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "vote_type",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          }
        ]
      },
      {
        "table_name": "profile_settings",
        "columns": [
          {
            "column_name": "setting_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('profile_settings_setting_id_seq'::regclass)"
          },
          {
            "column_name": "theme_preference",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": "'light'::text"
          },
          {
            "column_name": "notification_preference",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": "'all'::text"
          },
          {
            "column_name": "language",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": "'en'::text"
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "updated_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "now()"
          }
        ]
      },
      {
        "table_name": "category_course_counts",
        "columns": [
          {
            "column_name": "category_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "category_name",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "course_count",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "course_post_counts",
        "columns": [
          {
            "column_name": "course_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "course_name",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "post_count",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "post_comment_counts",
        "columns": [
          {
            "column_name": "post_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "comment_count",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "course_resource_counts",
        "columns": [
          {
            "column_name": "course_id",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "resource_count",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "votes",
        "columns": [
          {
            "column_name": "id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('votes_id_seq'::regclass)"
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "post_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "vote_type",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "comment_votes",
        "columns": [
          {
            "column_name": "vote_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('comment_votes_vote_id_seq'::regclass)"
          },
          {
            "column_name": "comment_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "user_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "vote_type",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": "now()"
          }
        ]
      },
      {
        "table_name": "post_reports",
        "columns": [
          {
            "column_name": "report_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": "nextval('post_reports_report_id_seq'::regclass)"
          },
          {
            "column_name": "post_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "reporter_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "reason",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": "now()"
          },
          {
            "column_name": "status",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": "'pending'::text"
          },
          {
            "column_name": "admin_notes",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "reviewed_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "django_session",
        "columns": [
          {
            "column_name": "session_key",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "session_data",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "expire_date",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": null
          }
        ]
      },
      {
        "table_name": "comment_reports",
        "columns": [
          {
            "column_name": "report_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "comment_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "reporter_id",
            "data_type": "bigint",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "reason",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": null
          },
          {
            "column_name": "description",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "status",
            "data_type": "text",
            "is_nullable": "NO",
            "column_default": "'pending'::text"
          },
          {
            "column_name": "admin_notes",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "NO",
            "column_default": "timezone('utc'::text, now())"
          },
          {
            "column_name": "reviewed_at",
            "data_type": "timestamp with time zone",
            "is_nullable": "YES",
            "column_default": null
          },
          {
            "column_name": "reviewed_by",
            "data_type": "bigint",
            "is_nullable": "YES",
            "column_default": null
          }
        ]
      }
    ]
  }
]