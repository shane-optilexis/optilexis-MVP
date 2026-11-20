"""Integration tests use an HTTP mock: no Azure account or charged request."""
import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from optilexis_api.live_text import AzureTextTranslator, LiveTextUnavailable
from optilexis_api.main import create_app
from .conftest import headers


@pytest.mark.asyncio
async def test_azure_transport_authenticated_and_formatted():
    observed = {}
    def responder(request):
        observed['url'] = str(request.url)
        observed['body'] = json.loads(request.content)
        observed['region'] = request.headers.get('ocp-apim-subscription-region')
        observed['key'] = request.headers.get('ocp-apim-subscription-key')
        return httpx.Response(200, json=[{'translations':[{'text':'Bonjour'}]}])
    provider = AzureTextTranslator('https://sample.cognitiveservices.azure.com/translator/text/v3.0/translate',
                                   'test-secret','eastus',httpx.MockTransport(responder))
    result = await provider.translate('Hello', 'en', 'fr')
    assert result == 'Bonjour'
    assert observed['body'] == [{'Text': 'Hello'}]
    assert observed['key'] == 'test-secret'
    assert observed['region'] == 'eastus'
    assert 'api-version=3.0' in observed['url']
    assert 'to=fr' in observed['url']


@pytest.mark.asyncio
async def test_azure_error_fails_closed():
    provider = AzureTextTranslator('https://sample.cognitiveservices.azure.com/translator/text/v3.0/translate',
                                   'test-secret','eastus',httpx.MockTransport(lambda request:httpx.Response(429,json={'error':'quota'})))
    with pytest.raises(LiveTextUnavailable, match='unavailable'):
        await provider.translate('Hello','en','fr')


def test_invalid_provider_endpoint_rejected(settings):
    enabled = replace(settings,text_translator='azure',azure_translator_endpoint='https://evil.example/translate',
                      azure_translator_key='test',azure_translator_region='eastus')
    with pytest.raises(ValueError,match='Azure Translator'):
        enabled.validate()


def test_translation_endpoints_owner_activation_vehicle_and_provider(settings):
    provider = AzureTextTranslator('https://sample.cognitiveservices.azure.com/translator/text/v3.0/translate',
                                   'test-secret','eastus',httpx.MockTransport(lambda request:
                                        httpx.Response(200,json=[{'translations':[{'text':'Bonjour'}]}])))
    enabled = replace(settings,text_translator='azure',azure_translator_endpoint=provider.endpoint,
                      azure_translator_key=provider.key,azure_translator_region=provider.region)
    with TestClient(create_app(enabled, text_translator_override=provider)) as app:
        j=app.post('/v1/journeys',headers=headers('alice'),json={'destination':'Tokyo Station','mode':'walk'}).json()['id']
        body={'journey_id':j,'text':'Hello','target_language':'fr','user_activated':True}
        assert app.post('/v1/translation/text',headers=headers('bob'),json=body).status_code == 404
        assert app.post('/v1/translation/text',headers=headers('alice'),json={**body,'user_activated':False}).status_code == 403
        ok=app.post('/v1/translation/text',headers=headers('alice'),json=body)
        assert ok.status_code == 200
        assert ok.json()['translated_text'] == 'Bonjour'
        assert ok.json()['simulated'] is False
        driving=app.post('/v1/journeys',headers=headers('alice'),json={'destination':'Hotel','mode':'drive'}).json()['id']
        assert app.post('/v1/translation/text',headers=headers('alice'),json={**body,'journey_id':driving}).status_code == 409
        assert app.post('/v1/translation/text',json=body).status_code == 401
    with TestClient(create_app(settings)) as app:
        j=app.post('/v1/journeys',headers=headers('alice'),json={'destination':'Tokyo Station','mode':'walk'}).json()['id']
        res=app.post('/v1/translation/text',headers=headers('alice'),json={**body,'journey_id':j})
        assert res.status_code==503
