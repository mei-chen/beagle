# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserLastViewDate'
        db.create_table(u'core_userlastviewdate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Document'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'core', ['UserLastViewDate'])


    def backwards(self, orm):
        # Deleting model 'UserLastViewDate'
        db.delete_table(u'core_userlastviewdate')


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
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'}),
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
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.batch': {
            'Meta': {'object_name': 'Batch'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'docs': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid_docs': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'trash': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'core.collaborationinvite': {
            'Meta': {'object_name': 'CollaborationInvite'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_received'", 'to': u"orm['auth.User']"}),
            'inviter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_sent'", 'to': u"orm['auth.User']"}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'sentence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Sentence']", 'null': 'True'})
        },
        u'core.collaboratorlist': {
            'Meta': {'object_name': 'CollaboratorList'},
            'collaborator_suggestions': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'collaborator_aggregate'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'core.delayednotification': {
            'Meta': {'object_name': 'DelayedNotification'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'notification': ('picklefield.fields.PickledObjectField', [], {}),
            'transient': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user_fields': ('jsonfield.fields.JSONField', [], {'default': "{'fields': []}"})
        },
        u'core.document': {
            'Meta': {'object_name': 'Document'},
            'agreement_type': ('django.db.models.fields.CharField', [], {'default': "'-'", 'max_length': '300', 'null': 'True'}),
            'agreement_type_confidence': ('django.db.models.fields.FloatField', [], {'default': '0.0', 'null': 'True'}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['core.Batch']", 'null': 'True', 'blank': 'True'}),
            'cached_analysis': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'dirty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doc_s3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'doclevel_analysis': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'docx_file': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'docx_s3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initsample': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'keywords_state': ('jsonfield.fields.JSONField', [], {'default': 'None', 'null': 'True'}),
            'learners_state': ('jsonfield.fields.JSONField', [], {'default': 'None', 'null': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'pdf_s3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'pending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'prepared': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'processing_begin_timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'processing_end_timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'sents': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'time_zone': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'trash': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'upload_source': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'core.externalinvite': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'ExternalInvite'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['core.Document']", 'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'email_sent_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'error_message': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '400', 'null': 'True', 'blank': 'True'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inviter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'pending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sentence': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['core.Sentence']", 'null': 'True'})
        },
        u'core.sentence': {
            'Meta': {'object_name': 'Sentence'},
            'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'annotations': ('jsonfield.fields.JSONField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'comments': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Document']"}),
            'extrefs': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'formatting': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likes': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'lock': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.SentenceLock']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'newlines': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'prev_revision': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'next_revision'", 'unique': 'True', 'null': 'True', 'to': u"orm['core.Sentence']"}),
            'rejected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'style': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        u'core.sentencelock': {
            'Meta': {'object_name': 'SentenceLock'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lifetime': ('django.db.models.fields.IntegerField', [], {'default': '60'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['auth.User']", 'null': 'True'})
        },
        u'core.userlastviewdate': {
            'Meta': {'object_name': 'UserLastViewDate'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['core']