# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'WrongAnalysisFlag.comments'
        db.alter_column(u'portal_wronganalysisflag', 'comments', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'WrongAnalysisFlag.resolution_comments'
        db.alter_column(u'portal_wronganalysisflag', 'resolution_comments', self.gf('django.db.models.fields.TextField')(null=True))

    def backwards(self, orm):

        # Changing field 'WrongAnalysisFlag.comments'
        db.alter_column(u'portal_wronganalysisflag', 'comments', self.gf('django.db.models.fields.TextField')())

        # Changing field 'WrongAnalysisFlag.resolution_comments'
        db.alter_column(u'portal_wronganalysisflag', 'resolution_comments', self.gf('django.db.models.fields.TextField')())

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.document': {
            'Meta': {'object_name': 'Document'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'dirty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doclevel_analysis': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'init_text': ('django.db.models.fields.TextField', [], {}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'pending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sents': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'trash': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.DocumentType']", 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'core.documenttype': {
            'Meta': {'object_name': 'DocumentType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'samples_folder': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '500'})
        },
        u'portal.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'avatar': ('django.db.models.fields.files.ImageField', [], {'default': "'../static/img/mug.png'", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_title': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'details'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'portal.wronganalysisflag': {
            'Meta': {'object_name': 'WrongAnalysisFlag'},
            'comments': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resolution_comments': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'resolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['portal']