# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Document.docx_file'
        db.add_column(u'core_document', 'docx_file',
                      self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Document.docx_file'
        db.delete_column(u'core_document', 'docx_file')


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
        u'core.collaborationinvite': {
            'Meta': {'object_name': 'CollaborationInvite'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_received'", 'to': u"orm['auth.User']"}),
            'inviter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_sent'", 'to': u"orm['auth.User']"}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        u'core.document': {
            'Meta': {'object_name': 'Document'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'dirty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doclevel_analysis': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'docx_file': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        u'core.sentence': {
            'Meta': {'object_name': 'Sentence'},
            'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Document']"}),
            'extrefs': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'formatting': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'labels': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'newline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'prev_revision': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'next_revision'", 'unique': 'True', 'null': 'True', 'to': u"orm['core.Sentence']"}),
            'rejected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['core']