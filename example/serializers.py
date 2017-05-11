from datetime import datetime
from rest_framework_json_api import serializers, relations
from example.models import Blog, Entry, Author, AuthorBio, Comment, TaggedItem


class TaggedItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaggedItem
        fields = ('tag', )


class BlogSerializer(serializers.ModelSerializer):

    copyright = serializers.SerializerMethodField()
    tags = TaggedItemSerializer(many=True, read_only=True)

    include_serializers = {
        'tags': 'example.serializers.TaggedItemSerializer',
    }

    def get_copyright(self, resource):
        return datetime.now().year

    def get_root_meta(self, resource, many):
        return {
            'api_docs': '/docs/api/blogs'
        }

    class Meta:
        model = Blog
        fields = ('name', 'url', 'tags')
        read_only_fields = ('tags', )
        meta_fields = ('copyright',)


class EntrySerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        # to make testing more concise we'll only output the
        # `featured` field when it's requested via `include`
        request = kwargs.get('context', {}).get('request')
        if request and 'featured' not in request.query_params.get('include', []):
            self.fields.pop('featured')
        super(EntrySerializer, self).__init__(*args, **kwargs)

    included_serializers = {
        'authors': 'example.serializers.AuthorSerializer',
        'comments': 'example.serializers.CommentSerializer',
        'featured': 'example.serializers.EntrySerializer',
        'suggested': 'example.serializers.EntrySerializer',
        'tags': 'example.serializers.TaggedItemSerializer',
    }

    body_format = serializers.SerializerMethodField()
    # many related from model
    comments = relations.ResourceRelatedField(
        many=True, read_only=True)
    # many related from serializer
    suggested = relations.SerializerMethodResourceRelatedField(
        source='get_suggested', model=Entry, many=True, read_only=True,
        related_link_view_name='entry-suggested',
        related_link_url_kwarg='entry_pk',
        self_link_view_name='entry-relationships',
    )
    # single related from serializer
    featured = relations.SerializerMethodResourceRelatedField(
        source='get_featured', model=Entry, read_only=True)
    tags = TaggedItemSerializer(many=True, read_only=True)

    def get_suggested(self, obj):
        return Entry.objects.exclude(pk=obj.pk)

    def get_featured(self, obj):
        return Entry.objects.exclude(pk=obj.pk).first()

    def get_body_format(self, obj):
        return 'text'

    class Meta:
        model = Entry
        fields = ('blog', 'headline', 'body_text', 'pub_date', 'mod_date',
                  'authors', 'comments', 'featured', 'suggested', 'tags')
        read_only_fields = ('tags', )
        meta_fields = ('body_format',)

    class JSONAPIMeta:
        included_resources = ['comments']


class AuthorBioSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthorBio
        fields = ('author', 'body',)


class AuthorSerializer(serializers.ModelSerializer):
    included_serializers = {
        'bio': AuthorBioSerializer
    }

    class Meta:
        model = Author
        fields = ('name', 'email', 'bio')


class WriterSerializer(serializers.ModelSerializer):
    included_serializers = {
        'bio': AuthorBioSerializer
    }

    class Meta:
        model = Author
        fields = ('name', 'email', 'bio')
        resource_name = 'writers'


class CommentSerializer(serializers.ModelSerializer):
    # testing remapping of related name
    writer = relations.ResourceRelatedField(source='author', read_only=True)

    included_serializers = {
        'entry': EntrySerializer,
        'author': AuthorSerializer,
        'writer': WriterSerializer
    }

    class Meta:
        model = Comment
        exclude = ('created_at', 'modified_at',)
        # fields = ('entry', 'body', 'author',)
